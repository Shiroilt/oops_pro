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