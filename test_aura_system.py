import sys
import os
import unittest
import json
import tempfile

# ── Path setup so imports resolve the same as main.py ──────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Redirect FileHandler to a temp file so tests never touch real data.json
import persistence.file_handler as _fh
_TEMP_DIR  = tempfile.mkdtemp()
_fh.DATA_FILE = os.path.join(_TEMP_DIR, "test_data.json")

# ── Now import everything ───────────────────────────────────────────────────
from persistence.file_handler import FileHandler
from core.central_registry   import CentralRegistry
from core.kiosk              import Kiosk, ActiveState, MaintenanceState, OfflineState, EMERGENCY_PURCHASE_LIMIT, EMERGENCY_STOCK_THRESHOLD
from core.kiosk_interface    import KioskInterface
from kiosk.kiosk_factory     import KioskFactory
from kiosk.food_kiosk        import FoodKiosk
from kiosk.pharmacy_kiosk    import PharmacyKiosk
from kiosk.emergency_kiosk   import EmergencyKiosk
from hardware.dispenser      import (BaseDispenser, RefrigerationModule,
                                     SolarModule, NetworkModule, HardwareDecorator)
from hardware.hardware_factory import HardwareFactory
from hardware.sensor         import SensorArray
from payment.adapter         import UPIAdapter, CardAdapter, DigitalWalletAdapter, payment_from_dict
from payment.payment_interface import PaymentProcessor
from product.product         import Product
from product.bundle          import ProductBundle
from product.inventory       import Inventory
from product.product_factory import ProductFactory, FoodProduct, PharmacyProduct, EmergencyProduct
from pricing.pricing_strategy import (PricingContext, StandardPricing,
                                       DiscountedPricing, EmergencyPricing, SurgePricing)
from commands.command        import Command, CommandHistory
from commands.purchase_command import PurchaseCommand
from commands.refund_command   import RefundCommand
from commands.restock_command  import RestockCommand
from city_monitor.monitor    import (EventBus, LowStockEvent, HardwareFailureEvent,
                                      EmergencyModeActivatedEvent, TransactionFailedEvent,
                                      RestockEvent, EventSubscriber, CityMonitoringCenter)
PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"

def make_food_kiosk(kiosk_id="TEST-FOOD", location="TestZone"):
    """Helper: create a ready-to-use FoodKiosk with UPI payment."""
    ki = KioskFactory.create_food_kiosk(kiosk_id, location)
    ki._kiosk.set_payment_processor(UPIAdapter("test@upi"))
    return ki

def make_pharmacy_kiosk(kiosk_id="TEST-PH", location="Hospital"):
    """Helper: create a ready-to-use PharmacyKiosk with UPI payment."""
    ki = KioskFactory.create_pharmacy_kiosk(kiosk_id, location)
    ki._kiosk.set_payment_processor(UPIAdapter("test@upi"))
    return ki

def make_emergency_kiosk(kiosk_id="TEST-EM", location="DisasterZone"):
    """Helper: create a ready-to-use EmergencyKiosk with UPI payment."""
    ki = KioskFactory.create_emergency_kiosk(kiosk_id, location)
    ki._kiosk.set_payment_processor(UPIAdapter("test@upi"))
    return ki

def fresh_product(name="Widget", price=50.0, stock=20,
                  chilled=False, pid="P001"):
    """Helper: create a fresh product instance."""
    return Product(pid, name, price, stock, chilled)

def fresh_registry():
    """Helper: reset the CentralRegistry singleton."""
    CentralRegistry._instance = None
    registry = CentralRegistry()
    registry.initialize()
    return registry

def fresh_event_bus():
    """Helper: reset EventBus singleton."""
    EventBus._instance = None
    return EventBus()

# ═══════════════════════════════════════════════════════════════════════════════
#   1. PERSISTENCE (Section 3.2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersistence(unittest.TestCase):
    """System must persist inventory, transaction history, and config to JSON."""

    def setUp(self):
        FileHandler.clear()

    def test_save_and_load_kiosk(self):
        """Saving a kiosk dict and loading it back returns the same data."""
        data = {"kiosk_type": "FoodKiosk", "location": "Metro", "inventory": []}
        FileHandler.save_kiosk("K001", data)
        loaded = FileHandler.load_kiosks()
        self.assertIn("K001", loaded)
        self.assertEqual(loaded["K001"]["location"], "Metro")

    def test_save_and_load_transaction(self):
        """Transactions are appended and retrievable."""
        FileHandler.save_transaction({
            "txn_id": "TXN-001", "kiosk_id": "K001",
            "user_id": "u1", "item": "Water", "amount": 20.0,
            "type": "PURCHASE", "status": "SUCCESS", "timestamp": "2024-01-01"
        })
        txns = FileHandler.load_transactions()
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]["txn_id"], "TXN-001")

    def test_multiple_transactions_accumulate(self):
        """Multiple saves accumulate, not overwrite."""
        for i in range(3):
            FileHandler.save_transaction({
                "txn_id": f"T{i}", "kiosk_id": "K1",
                "user_id": "u1", "item": "X", "amount": 10.0,
                "type": "PURCHASE", "status": "SUCCESS", "timestamp": "2024-01-01"
            })
        self.assertEqual(len(FileHandler.load_transactions()), 3)

    def test_save_config(self):
        """Config is stored inside the JSON file."""
        data = FileHandler.load()
        data["config"]["max_items"] = 50
        FileHandler.save(data)
        reloaded = FileHandler.load()
        self.assertEqual(reloaded["config"]["max_items"], 50)

    def test_inventory_persisted_via_kiosk(self):
        """Kiosk state including inventory is persisted on purchase."""
        ki = make_food_kiosk("PERSIST-01")
        ki.purchase_item("Water Bottle", "user_test")
        saved = FileHandler.load_kiosks()
        self.assertIn("PERSIST-01", saved)
        inv_list = saved["PERSIST-01"].get("inventory", [])
        names = [i["name"] for i in inv_list if i.get("type") != "bundle"]
        self.assertIn("Water Bottle", names)

# ═══════════════════════════════════════════════════════════════════════════════
#   2. CENTRAL REGISTRY + FACTORY (Section 3.3, 3.4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCentralRegistry(unittest.TestCase):
    """CentralRegistry must behave as a Singleton and track system state."""

    def setUp(self):
        CentralRegistry._instance = None
        self.registry = CentralRegistry()
        self.registry.initialize()

    def test_singleton_instance(self):
        """Multiple instances should point to same object."""
        r2 = CentralRegistry()
        self.assertIs(self.registry, r2)

    def test_register_kiosk(self):
        """Registering kiosks should store them globally."""
        ki = make_food_kiosk("REG-01")
        self.registry.register_kiosk(ki._kiosk)

        kiosks = self.registry.get_all_kiosks()
        self.assertIn("REG-01", kiosks)

    def test_transaction_logging(self):
        """Transactions should be recorded globally."""
        ki = make_food_kiosk("REG-02")
        ki.purchase_item("Water Bottle", "user1")

        txns = self.registry.get_all_transactions()
        self.assertGreater(len(txns), 0)


class TestKioskFactory(unittest.TestCase):
    """Factory must correctly instantiate kiosk types with proper setup."""

    def test_food_kiosk_creation(self):
        ki = KioskFactory.create_food_kiosk("F-01", "Metro")
        self.assertIsInstance(ki._kiosk, FoodKiosk)

    def test_pharmacy_kiosk_creation(self):
        ki = KioskFactory.create_pharmacy_kiosk("P-01", "Hospital")
        self.assertIsInstance(ki._kiosk, PharmacyKiosk)

    def test_emergency_kiosk_creation(self):
        ki = KioskFactory.create_emergency_kiosk("E-01", "Disaster Zone")
        self.assertIsInstance(ki._kiosk, EmergencyKiosk)

    def test_factory_initializes_inventory(self):
        """Factory should preload inventory for kiosks."""
        ki = KioskFactory.create_food_kiosk("F-02", "Campus")
        items = ki._kiosk.inventory.get_all_items()
        self.assertGreater(len(items), 0)

# ═══════════════════════════════════════════════════════════════════════════════
#   3. KIOSK INTERFACE (FACADE PATTERN)
# ═══════════════════════════════════════════════════════════════════════════════

class TestKioskInterface(unittest.TestCase):
    """Tests for Facade layer handling all kiosk operations."""

    def setUp(self):
        FileHandler.clear()
        self.ki = make_food_kiosk("FACADE-01")

    def test_purchase_success(self):
        """Valid purchase should succeed and be recorded."""
        result = self.ki.purchase_item("Water Bottle", "user1")
        self.assertTrue(result)

        txns = FileHandler.load_transactions()
        self.assertEqual(len(txns), 1)

    def test_purchase_invalid_item(self):
        """Purchasing non-existing item should fail."""
        result = self.ki.purchase_item("Invalid Item", "user1")
        self.assertFalse(result)

    def test_purchase_insufficient_stock(self):
        """Requesting more than available stock should fail."""
        result = self.ki.purchase_item("Water Bottle", "user1", quantity=1000)
        self.assertFalse(result)

    def test_refund_transaction(self):
        """Refund should succeed for valid transaction."""
        self.ki.purchase_item("Water Bottle", "user1")

        txns = FileHandler.load_transactions()
        txn_id = txns[0]["txn_id"]

        result = self.ki.refund_transaction(txn_id, "user1")
        self.assertTrue(result)

    def test_restock_inventory(self):
        """Admin should be able to restock items."""
        result = self.ki.restock_inventory("Water Bottle", 10)
        self.assertTrue(result)

    def test_get_user_transactions(self):
        """Should return only transactions for given user."""
        self.ki.purchase_item("Water Bottle", "userA")
        self.ki.purchase_item("Water Bottle", "userB")

        user_a_txns = self.ki.get_user_transactions("userA")
        self.assertEqual(len(user_a_txns), 1)

# ═══════════════════════════════════════════════════════════════════════════════
#   4. COMMAND PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommandPattern(unittest.TestCase):
    """Tests for Command pattern execution and history tracking."""

    def setUp(self):
        FileHandler.clear()
        self.registry = fresh_registry()
        self.ki = make_food_kiosk("CMD-01")
        self.kiosk = self.ki._kiosk

    def test_purchase_command_execution(self):
        """PurchaseCommand should execute and reduce stock."""
        item = self.kiosk._inventory.find_item("Water Bottle")
        initial_stock = item.get_available_stock()

        cmd = PurchaseCommand(
            kiosk_id=self.kiosk.kiosk_id,
            user_id="user1",
            item=item,
            payment_processor=self.kiosk._payment_processor,
            pricing_context=self.kiosk._pricing,
            kiosk_ref=self.kiosk,
        )

        result = cmd.execute()
        self.assertTrue(result)

        self.assertEqual(item.get_available_stock(), initial_stock - 1)

    def test_refund_command_execution(self):
        """RefundCommand should restore stock."""
        self.ki.purchase_item("Water Bottle", "user1")

        txns = FileHandler.load_transactions()
        txn_id = txns[0]["txn_id"]

        item = self.kiosk._inventory.find_item("Water Bottle")
        stock_before = item.get_available_stock()

        cmd = RefundCommand(
            kiosk_id=self.kiosk.kiosk_id,
            user_id="user1",
            txn_id=txn_id,
            item=item,
            payment_processor=self.kiosk._payment_processor,
        )

        result = cmd.execute()
        self.assertTrue(result)

        self.assertGreater(item.get_available_stock(), stock_before)

    def test_restock_command_execution(self):
        """RestockCommand should increase stock."""
        item = self.kiosk._inventory.find_item("Water Bottle")
        initial_stock = item.get_available_stock()

        cmd = RestockCommand(
            kiosk_id=self.kiosk.kiosk_id,
            user_id="admin",
            item=item,
            quantity=5,
        )

        result = cmd.execute()
        self.assertTrue(result)

        self.assertEqual(item.get_available_stock(), initial_stock + 5)

    def test_command_history_tracking(self):
        """CommandHistory should record executed commands."""
        history = CommandHistory()

        item = self.kiosk._inventory.find_item("Water Bottle")

        cmd = PurchaseCommand(
            kiosk_id=self.kiosk.kiosk_id,
            user_id="user1",
            item=item,
            payment_processor=self.kiosk._payment_processor,
            pricing_context=self.kiosk._pricing,
            kiosk_ref=self.kiosk,
        )

        cmd.execute()
        history.record(cmd)

        self.assertEqual(len(history._history), 1)

    def test_multiple_commands_sequence(self):
        """Multiple commands should execute correctly in sequence."""
        item = self.kiosk._inventory.find_item("Water Bottle")
        initial_stock = item.get_available_stock()

        for _ in range(3):
            cmd = PurchaseCommand(
                kiosk_id=self.kiosk.kiosk_id,
                user_id="user1",
                item=item,
                payment_processor=self.kiosk._payment_processor,
                pricing_context=self.kiosk._pricing,
                kiosk_ref=self.kiosk,
            )
            cmd.execute()

        self.assertEqual(item.get_available_stock(), initial_stock - 3)

# ═══════════════════════════════════════════════════════════════════════════════
#   5. DERIVED ATTRIBUTES + SYSTEM CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDerivedAttributes(unittest.TestCase):
    """Tests for computed/derived values like stock and availability."""

    def test_product_available_stock(self):
        """Available stock = total stock - reserved."""
        p = fresh_product(stock=10)

        p.reserve()
        p.reserve()

        self.assertEqual(p.get_available_stock(), 8)

    def test_product_unavailable_due_to_hardware(self):
        """Product becomes unavailable if hardware dependency fails."""
        p = fresh_product(chilled=True)
        p.mark_hardware_unavailable(True)

        self.assertFalse(p.is_available())
        self.assertEqual(p.get_available_stock(), 0)

    def test_bundle_stock_minimum(self):
        """Bundle stock should be minimum of its items."""
        p1 = fresh_product(stock=10)
        p2 = fresh_product(stock=5)

        bundle = ProductBundle("B1", "Test Bundle")
        bundle.add_item(p1)
        bundle.add_item(p2)

        self.assertEqual(bundle.get_available_stock(), 5)

    def test_bundle_price_with_discount(self):
        """Bundle price should apply discount correctly."""
        p1 = fresh_product(price=100)
        p2 = fresh_product(price=100)

        bundle = ProductBundle("B2", "Discount Bundle", discount_pct=10)
        bundle.add_item(p1)
        bundle.add_item(p2)

        self.assertEqual(bundle.get_price(), 180.0)


class TestSystemConstraints(unittest.TestCase):
    """Tests for system rules like limits and emergency mode."""

    def setUp(self):
        self.ki = make_food_kiosk("CONST-01")

    def test_daily_purchase_limit(self):
        """User should not exceed daily purchase limit."""
        for _ in range(10):
            self.ki.purchase_item("Water Bottle", "user1")

        result = self.ki.purchase_item("Water Bottle", "user1")
        self.assertFalse(result)

    def test_emergency_mode_limit(self):
        """Emergency mode should enforce stricter limits."""
        kiosk = self.ki._kiosk
        kiosk._emergency_mode = True

        for _ in range(EMERGENCY_PURCHASE_LIMIT):
            self.ki.purchase_item("Water Bottle", "user1")

        result = self.ki.purchase_item("Water Bottle", "user1")
        self.assertFalse(result)

    def test_emergency_activation_on_low_stock(self):
        """Emergency mode activates when stock is too low."""
        kiosk = self.ki._kiosk
        item = kiosk._inventory.find_item("Water Bottle")

        # Reduce stock below threshold
        while item.get_available_stock() > EMERGENCY_STOCK_THRESHOLD:
            item.confirm_sale()

        kiosk.check_and_activate_emergency()
        self.assertTrue(kiosk._emergency_mode)