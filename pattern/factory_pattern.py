"""
DESIGN PATTERN: Factory Method
File: patterns/factory_pattern.py
Purpose: KioskFactory creates fully configured kiosk objects (with hardware,
         payment, and inventory) for each kiosk type.
         Callers never manually assemble kiosk components.
"""

from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from hardware.hardware_factory import HardwareFactory
from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from product.product import Product
from product.bundle import ProductBundle
from product.inventory import Inventory


class KioskFactory:
    """
    Factory Method: Each create_*_kiosk method returns a ready-to-use
    KioskInterface with compatible components already wired together.
    """

    @staticmethod
    def create_food_kiosk(kiosk_id: str, location: str) -> KioskInterface:
        """Create a fully configured food/metro kiosk."""
        kiosk = Kiosk(kiosk_id, location, "FoodKiosk")

        # Hardware
        hardware, sensors = HardwareFactory.create_food_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hardware)

        # Payment — UPI is standard for metro food kiosks
        kiosk.set_payment_processor(UPIAdapter(vpa=f"{kiosk_id}@cityupi"))

        # Inventory
        inv = Inventory()
        inv.add_item(Product("F001", "Water Bottle", 20.0, stock=100))
        inv.add_item(Product("F002", "Sandwich", 60.0, stock=30, requires_refrigeration=True))
        inv.add_item(Product("F003", "Chips", 25.0, stock=50))
        meal_deal = ProductBundle("B001", "Meal Deal", discount_pct=10)
        meal_deal.add_item(Product("F002b", "Sandwich", 60.0, stock=30, requires_refrigeration=True))
        meal_deal.add_item(Product("F003b", "Chips", 25.0, stock=50))
        inv.add_item(meal_deal)
        kiosk.set_inventory(inv.get_all_items())

        print(f"[KioskFactory] FoodKiosk '{kiosk_id}' created at {location}")
        return KioskInterface(kiosk)

    @staticmethod
    def create_pharmacy_kiosk(kiosk_id: str, location: str) -> KioskInterface:
        """Create a fully configured pharmacy kiosk."""
        kiosk = Kiosk(kiosk_id, location, "PharmacyKiosk")

        hardware, sensors = HardwareFactory.create_pharmacy_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hardware)

        # Payment — card for hospitals
        kiosk.set_payment_processor(CardAdapter(card_token="VISA-HOSP-0001"))

        inv = Inventory()
        inv.add_item(Product("M001", "Paracetamol 500mg", 45.0, stock=100))
        inv.add_item(Product("M002", "Cough Syrup", 120.0, stock=40))
        inv.add_item(Product("M003", "Bandage Roll", 35.0, stock=60))
        kiosk.set_inventory(inv.get_all_items())

        print(f"[KioskFactory] PharmacyKiosk '{kiosk_id}' created at {location}")
        return KioskInterface(kiosk)

    @staticmethod
    def create_emergency_kiosk(kiosk_id: str, location: str) -> KioskInterface:
        """Create a fully configured emergency relief kiosk."""
        kiosk = Kiosk(kiosk_id, location, "EmergencyKiosk")

        hardware, sensors = HardwareFactory.create_emergency_kiosk_hardware(kiosk_id)
        kiosk.set_hardware(hardware)

        # Emergency kiosks use digital wallet
        kiosk.set_payment_processor(DigitalWalletAdapter(wallet_id="RELIEF-FUND-01"))

        inv = Inventory()
        inv.add_item(Product("E001", "Ration Pack", 0.0, stock=200))     # free in emergency
        inv.add_item(Product("E002", "Water Pouch", 0.0, stock=500))
        inv.add_item(Product("E003", "First Aid Kit", 0.0, stock=80))

        # Emergency bundle
        relief_kit = ProductBundle("EB01", "Emergency Relief Bundle", discount_pct=0)
        relief_kit.add_item(Product("E001b", "Ration Pack", 0.0, stock=200))
        relief_kit.add_item(Product("E002b", "Water Pouch", 0.0, stock=500))
        relief_kit.add_item(Product("E003b", "First Aid Kit", 0.0, stock=80))
        inv.add_item(relief_kit)
        kiosk.set_inventory(inv.get_all_items())

        print(f"[KioskFactory] EmergencyKiosk '{kiosk_id}' created at {location}")
        return KioskInterface(kiosk)
