"""
DESIGN PATTERN: Factory Method
File: kiosk/kiosk_factory.py
Purpose: KioskFactory builds fully wired kiosks by type.
         Each create_*() method is a Factory Method that decides which
         concrete Kiosk subclass and hardware stack to assemble.
         Also supports rebuilding kiosks from saved JSON (restore_from_dict).

NOTE: Payment is NOT set here. Users select payment at purchase time.
"""

from core.kiosk_interface import KioskInterface
from kiosk.food_kiosk import FoodKiosk
from kiosk.pharmacy_kiosk import PharmacyKiosk
from kiosk.emergency_kiosk import EmergencyKiosk
from hardware.hardware_factory import HardwareFactory
from payment.adapter import payment_from_dict
from product.inventory import Inventory
from product.product import Product
from product.bundle import ProductBundle
from product.product_factory import ProductFactory


class KioskFactory:
    """
    FACTORY METHOD: Each create_* method is a factory method that
    produces a fully configured KioskInterface for a specific kiosk type.
    """

    @staticmethod
    def create_food_kiosk(kiosk_id: str, location: str, password: str = "1234") -> KioskInterface:
        """Factory Method: builds a Food Kiosk with default inventory."""
        kiosk = FoodKiosk(kiosk_id, location, password)
        hw, sensors = HardwareFactory.create_food_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hw)
        kiosk.set_sensors(sensors)
        kiosk.set_payment_processor(None)   # user picks at purchase time

        inv = Inventory()
        inv.add_item(ProductFactory.create_product("FoodKiosk", "Water Bottle", 20.0, 50))
        inv.add_item(ProductFactory.create_product("FoodKiosk", "Sandwich",     60.0, 20,
                                                   requires_refrigeration=True))
        inv.add_item(ProductFactory.create_product("FoodKiosk", "Chips",        25.0, 40))

        combo = ProductBundle("C001", "Meal Combo", discount_pct=10)
        combo.add_item(Product("FC1", "Sandwich", 60.0, 20, requires_refrigeration=True))
        combo.add_item(Product("FC2", "Chips",    25.0, 40))
        inv.add_item(combo)

        kiosk.set_inventory(inv)
        print(f"[KioskFactory] FoodKiosk '{kiosk_id}' ready at {location}")
        return KioskInterface(kiosk)

    @staticmethod
    def create_pharmacy_kiosk(kiosk_id: str, location: str, password: str = "1234") -> KioskInterface:
        """Factory Method: builds a Pharmacy Kiosk with default inventory."""
        kiosk = PharmacyKiosk(kiosk_id, location, password)
        hw, sensors = HardwareFactory.create_pharmacy_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hw)
        kiosk.set_sensors(sensors)
        kiosk.set_payment_processor(None)

        inv = Inventory()
        inv.add_item(ProductFactory.create_product("PharmacyKiosk", "Paracetamol 500mg", 45.0, 100))
        inv.add_item(ProductFactory.create_product("PharmacyKiosk", "Cough Syrup",       120.0, 40))
        inv.add_item(ProductFactory.create_product("PharmacyKiosk", "Bandage Roll",       35.0, 60))

        combo = ProductBundle("C002", "First Aid Combo", discount_pct=5)
        combo.add_item(Product("PC1", "Bandage Roll", 35.0, 60))
        combo.add_item(Product("PC2", "Antiseptic",   40.0, 50))
        inv.add_item(combo)

        kiosk.set_inventory(inv)
        print(f"[KioskFactory] PharmacyKiosk '{kiosk_id}' ready at {location}")
        return KioskInterface(kiosk)

    @staticmethod
    def create_emergency_kiosk(kiosk_id: str, location: str, password: str = "1234") -> KioskInterface:
        """Factory Method: builds an Emergency Kiosk with free essential items."""
        kiosk = EmergencyKiosk(kiosk_id, location, password)
        hw, sensors = HardwareFactory.create_emergency_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hw)
        kiosk.set_sensors(sensors)
        kiosk.set_payment_processor(None)

        inv = Inventory()
        inv.add_item(ProductFactory.create_product("EmergencyKiosk", "Ration Pack",    0.0, 200))
        inv.add_item(ProductFactory.create_product("EmergencyKiosk", "Water Pouch",    0.0, 500))
        inv.add_item(ProductFactory.create_product("EmergencyKiosk", "First Aid Kit",  0.0, 80))

        combo = ProductBundle("C003", "Emergency Bundle", discount_pct=0)
        combo.add_item(Product("EC1", "Ration Pack",   0.0, 200))
        combo.add_item(Product("EC2", "Water Pouch",   0.0, 500))
        combo.add_item(Product("EC3", "First Aid Kit", 0.0, 80))
        inv.add_item(combo)

        kiosk.set_inventory(inv)
        print(f"[KioskFactory] EmergencyKiosk '{kiosk_id}' ready at {location}")
        return KioskInterface(kiosk)

    @staticmethod
    def restore_from_dict(kiosk_id: str, data: dict) -> KioskInterface:
        """Rebuild a kiosk from saved JSON data."""
        ktype    = data.get("kiosk_type", "FoodKiosk")
        location = data.get("location", "Unknown")
        password = data.get("password", "1234")

        if ktype == "PharmacyKiosk":
            kiosk = PharmacyKiosk(kiosk_id, location, password)
        elif ktype == "EmergencyKiosk":
            kiosk = EmergencyKiosk(kiosk_id, location, password)
        else:
            kiosk = FoodKiosk(kiosk_id, location, password)

        modules = data.get("hardware_modules", [])
        hw, sensors = HardwareFactory.create_custom_hardware(kiosk_id, modules)
        kiosk.set_hardware(hw)
        kiosk.set_sensors(sensors)

        # Payment restored if present, else None (user picks at purchase)
        payment_data = data.get("payment", {})
        if payment_data:
            payment = payment_from_dict(payment_data)
        else:
            payment = None
        kiosk.set_payment_processor(payment)

        inv = Inventory.from_list(data.get("inventory", []))
        kiosk.set_inventory(inv)

        return KioskInterface(kiosk)
