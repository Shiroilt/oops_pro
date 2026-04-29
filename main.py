"""
File: main.py
AURA RETAIL OS — Smart City Modular Kiosk Platform

Flow:
  - Ask role: User or Admin at startup
  - Admin: password check (root) → full access (create/add/restock/hardware/models)
  - User: direct to vending machine menu (buy/refund/view only)
  - Payment is selected by user AT PURCHASE TIME (not at kiosk creation)
  - All data saved to persistence/data.json automatically
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.central_registry import CentralRegistry
from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from persistence.file_handler import FileHandler
from kiosk.kiosk_factory import KioskFactory
from hardware.hardware_factory import HardwareFactory
from hardware.dispenser import BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from payment.payment_selector import PaymentSelector
from product.product import Product
from product.bundle import ProductBundle
from product.inventory import Inventory
from product.product_factory import ProductFactory
from kiosk.food_kiosk import FoodKiosk
from kiosk.pharmacy_kiosk import PharmacyKiosk
from kiosk.emergency_kiosk import EmergencyKiosk
from city_monitor.monitor import EventBus
from pricing.pricing_strategy import (
    PricingContext, StandardPricing, DiscountedPricing,
    EmergencyPricing, SurgePricing
)

ADMIN_PASSWORD = "root"


# ── UI Helpers ────────────────────────────────────────────────────────────────

def divider(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def line():
    print("-" * 60)

def get_choice(prompt: str, valid: list) -> str:
    while True:
        c = input(prompt).strip()
        if c in valid:
            return c
        print(f"  Invalid. Choose from: {valid}")

def pause():
    input("\n  Press Enter to continue...")

def ask(prompt: str, default: str = "") -> str:
    val = input(f"  {prompt}").strip()
    return val if val else default


# ── Startup: Role Selection ───────────────────────────────────────────────────

def startup() -> tuple:
    """Ask role at startup. Return (role, user_id)."""
    registry = CentralRegistry()
    registry.initialize()

    print("\n" + "=" * 60)
    print("   AURA RETAIL OS")
    print("   Smart City Modular Kiosk Platform")
    print("=" * 60)

    print("\n  Who are you?")
    print("    1. User   — Browse & purchase from vending machines")
    print("    2. Admin  — Full system management (password required)")
    line()
    role_choice = get_choice("  Select (1/2): ", ["1", "2"])

    if role_choice == "2":
        # Admin path: password check
        for attempt in range(3):
            pwd = input("  Enter admin password: ").strip()
            if pwd == ADMIN_PASSWORD:
                print("\n  Admin access granted.")
                admin_id = ask("  Admin ID (e.g. admin_01): ", "admin_01")
                print(f"\n  Welcome, Admin {admin_id}!")
                return "admin", admin_id
            else:
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"  Wrong password. {remaining} attempt(s) left.")
                else:
                    print("  Too many failed attempts. Switching to User mode.")
                    break

    # User path
    user_id = ask("Enter your User ID (e.g. user_01): ", "guest_user")
    print(f"\n  Welcome, {user_id}!")
    return "user", user_id


# ── Load saved kiosks ─────────────────────────────────────────────────────────

def load_saved_kiosks() -> dict:
    saved = FileHandler.load_kiosks()
    active = {}
    for kid, data in saved.items():
        try:
            ki = KioskFactory.restore_from_dict(kid, data)
            active[kid] = ki
        except Exception as e:
            print(f"  [Warning] Could not restore kiosk {kid}: {e}")
    if active:
        print(f"\n  Loaded {len(active)} saved kiosk(s): {list(active.keys())}")
    return active


# ════════════════════════════════════════════════════════════
#   ADMIN FLOWS
# ════════════════════════════════════════════════════════════

def admin_main_menu(active_kiosks: dict, admin_id: str):
    """Full admin menu — all management functions."""
    while True:
        divider(f"ADMIN MENU — {admin_id}")
        print(f"\n  Active kiosks: {len(active_kiosks)}")
        print("\n  1. Create New Vending Machine")
        print("  2. Add Item to Existing Kiosk")
        print("  3. Restock Item in Kiosk")
        print("  4. Add Combo/Bundle to Kiosk")
        print("  5. Add Hardware Module to Kiosk")
        print("  6. Change Kiosk Model (Type)")
        print("  7. View/Use Vending Machine")
        print("  8. City Monitor Events")
        print("  9. System Registry Summary")
        print("  0. Exit")
        line()

        c = get_choice("  Select (0-9): ", [str(i) for i in range(10)])

        if   c == "1": admin_create_kiosk(active_kiosks, admin_id)
        elif c == "2": admin_add_item(active_kiosks)
        elif c == "3": admin_restock(active_kiosks, admin_id)
        elif c == "4": admin_add_combo(active_kiosks)
        elif c == "5": admin_add_hardware(active_kiosks)
        elif c == "6": admin_change_model(active_kiosks)
        elif c == "7":
            if not active_kiosks:
                print("\n  No kiosks found. Create one first.")
                pause()
            else:
                ki = select_kiosk(active_kiosks)
                if _check_kiosk_password(ki):
                    admin_kiosk_menu(ki, admin_id, active_kiosks)
        elif c == "8": do_city_monitor()
        elif c == "9": do_registry_summary()
        elif c == "0":
            print("\n  Saving all data...")
            for kid, ki in active_kiosks.items():
                ki._save_kiosk_state()
            print("  All kiosks saved. Goodbye!\n")
            sys.exit(0)


def admin_create_kiosk(active_kiosks: dict, admin_id: str):
    """Admin: Create a brand new kiosk (no payment set at creation — user picks at purchase)."""
    divider("CREATE NEW VENDING MACHINE")

    print("\n  Kiosk types:")
    print("    1. Food Kiosk       (Metro/Campus)")
    print("    2. Pharmacy Kiosk   (Hospital)")
    print("    3. Emergency Kiosk  (Disaster Zone)")
    line()
    ktype = get_choice("  Choose type (1/2/3): ", ["1", "2", "3"])
    type_map = {"1": "FoodKiosk", "2": "PharmacyKiosk", "3": "EmergencyKiosk"}
    ktype_name = type_map[ktype]

    kiosk_id = ask(f"  Kiosk ID (e.g. KIOSK-01): ",
                   f"KIOSK-{len(active_kiosks)+1:02d}").upper()
    location = ask("  Location (e.g. Central Metro): ", "City Zone")
    password = ask("  Kiosk Admin Password: ", "1234")

    # Items
    items = _collect_items()

    # Combos
    combos = _collect_combos(items)

    # Hardware
    hw, sensors, modules = _collect_hardware(kiosk_id)

    # Assemble
    divider("CREATING KIOSK...")
    if ktype_name == "PharmacyKiosk":
        kiosk = PharmacyKiosk(kiosk_id, location, password)
    elif ktype_name == "EmergencyKiosk":
        kiosk = EmergencyKiosk(kiosk_id, location, password)
    else:
        kiosk = FoodKiosk(kiosk_id, location, password)

    kiosk.set_hardware(hw)
    kiosk.set_sensors(sensors)
    # No payment set here — user selects at purchase time
    kiosk.set_payment_processor(None)

    inv = Inventory()
    for item in items:
        inv.add_item(item)
    for combo in combos:
        inv.add_item(combo)
    kiosk.set_inventory(inv)

    ki = KioskInterface(kiosk)
    active_kiosks[kiosk_id] = ki
    ki._save_kiosk_state()

    print(f"\n  Kiosk '{kiosk_id}' created and saved!")
    print("  NOTE: Payment method is selected by users at purchase time.")
    ki.show_kiosk_info()
    ki.show_inventory()
    pause()


def admin_add_item(active_kiosks: dict):
    """Admin: Add a new item to an existing kiosk."""
    if not active_kiosks:
        print("\n  No kiosks available.")
        pause()
        return
    divider("ADD ITEM TO KIOSK")
    ki = select_kiosk(active_kiosks)
    if not _check_kiosk_password(ki):
        return
    inv = ki._kiosk._inventory

    name = ask("  New item name: ", "")
    if not name:
        return
    try:
        price = float(ask(f"  Price for '{name}' (Rs.): ", "0"))
        qty   = int(ask(f"  Quantity: ", "10"))
    except ValueError:
        print("  Invalid input.")
        pause()
        return

    needs_fridge = get_choice(
        f"  Needs refrigeration? (y/n): ", ["y", "n"]
    ) == "y"

    # Use Abstract Factory to create the right product family
    ktype = ki._kiosk.kiosk_type
    item = ProductFactory.create_product(ktype, name, price, qty, needs_fridge)
    inv.add_item(item)
    if ki._kiosk._hardware:
        inv.enforce_hardware_constraints(ki._kiosk._hardware.get_capabilities())

    ki._save_kiosk_state()
    print(f"\n  Item '{name}' added to kiosk '{ki._kiosk.kiosk_id}'.")
    pause()


def admin_restock(active_kiosks: dict, admin_id: str):
    """Admin: Restock an item in a kiosk."""
    if not active_kiosks:
        print("\n  No kiosks available.")
        pause()
        return
    divider("RESTOCK ITEM")
    ki = select_kiosk(active_kiosks)
    if not _check_kiosk_password(ki):
        return
    ki.show_inventory()
    line()

    name = ask("  Item name to restock: ", "")
    if not name:
        return
    try:
        qty = int(ask("  Quantity to add: ", "10"))
    except ValueError:
        print("  Invalid quantity.")
        pause()
        return

    ki.restock_inventory(name, qty, admin_id=admin_id)
    pause()


def admin_add_combo(active_kiosks: dict):
    """Admin: Add a combo/bundle to an existing kiosk."""
    if not active_kiosks:
        print("\n  No kiosks available.")
        pause()
        return
    divider("ADD COMBO TO KIOSK")
    ki = select_kiosk(active_kiosks)
    if not _check_kiosk_password(ki):
        return
    inv = ki._kiosk._inventory

    # Get individual products only
    products = [i for i in inv.get_all_items() if isinstance(i, Product)]
    if not products:
        print("\n  No individual items available to build a combo.")
        pause()
        return

    combo_name = ask("  Combo name (e.g. 'Meal Deal'): ", "")
    if not combo_name:
        return
    try:
        discount = float(ask("  Discount % (e.g. 10): ", "0"))
    except ValueError:
        discount = 0.0

    print("\n  Available items:")
    for i, item in enumerate(products, 1):
        print(f"    {i}. {item.get_name()} — Rs.{item.get_price():.2f}")
    line()

    combo_items = []
    print("  Enter item numbers to include. Type '0' when done.")
    while True:
        try:
            choice = int(ask("  Item number (0 to finish): ", "0"))
            if choice == 0:
                break
            if 1 <= choice <= len(products):
                combo_items.append(products[choice - 1])
                print(f"  Added '{products[choice-1].get_name()}'")
            else:
                print(f"  Choose 1–{len(products)}")
        except ValueError:
            break

    if combo_items:
        all_items = inv.get_all_items()
        bid = f"C{len([i for i in all_items if isinstance(i, ProductBundle)])+1:03d}"
        bundle = ProductBundle(bid, combo_name, discount_pct=discount)
        for ci in combo_items:
            bundle.add_item(ci)
        inv.add_item(bundle)
        ki._save_kiosk_state()
        print(f"\n  Combo '{combo_name}' added with {len(combo_items)} items.")
    else:
        print("\n  No items selected, combo not created.")
    pause()


def admin_add_hardware(active_kiosks: dict):
    """Admin: Add a hardware module to an existing kiosk."""
    if not active_kiosks:
        print("\n  No kiosks available.")
        pause()
        return
    divider("ADD HARDWARE MODULE")
    ki = select_kiosk(active_kiosks)
    if not _check_kiosk_password(ki):
        return
    kiosk = ki._kiosk

    existing = kiosk._hardware.get_capabilities() if kiosk._hardware else []
    print(f"\n  Existing capabilities: {existing}")
    print("\n  Add module:")
    print("    1. Refrigeration")
    print("    2. Solar Power")
    print("    3. Network")
    print("    0. Cancel")
    line()

    c = get_choice("  Select (0-3): ", ["0", "1", "2", "3"])
    if c == "0":
        return

    hw = kiosk._hardware or BaseDispenser(kiosk.kiosk_id)

    if c == "1":
        if "refrigeration" not in existing:
            hw = RefrigerationModule(hw, target_temp_c=4.0)
            print("  Refrigeration module added.")
        else:
            print("  Already has refrigeration.")
    elif c == "2":
        if "solar_power" not in existing:
            hw = SolarModule(hw)
            print("  Solar power module added.")
        else:
            print("  Already has solar power.")
    elif c == "3":
        if "network" not in existing:
            ssid = ask("  Network SSID: ", "CityNet")
            hw = NetworkModule(hw, ssid=ssid)
            print("  Network module added.")
        else:
            print("  Already has network.")

    kiosk.set_hardware(hw)
    ki._save_kiosk_state()
    print(f"  Updated capabilities: {kiosk._hardware.get_capabilities()}")
    pause()


def admin_change_model(active_kiosks: dict):
    """Admin: Change kiosk type/model."""
    if not active_kiosks:
        print("\n  No kiosks available.")
        pause()
        return
    divider("CHANGE KIOSK MODEL")
    ki = select_kiosk(active_kiosks)
    if not _check_kiosk_password(ki):
        return
    kiosk = ki._kiosk

    print(f"\n  Current model: {kiosk.kiosk_type}")
    print("  New model:")
    print("    1. Food Kiosk")
    print("    2. Pharmacy Kiosk")
    print("    3. Emergency Kiosk")
    print("    0. Cancel")
    line()
    c = get_choice("  Select (0-3): ", ["0", "1", "2", "3"])
    if c == "0":
        return

    type_map = {"1": "FoodKiosk", "2": "PharmacyKiosk", "3": "EmergencyKiosk"}
    new_type = type_map[c]

    if new_type == kiosk.kiosk_type:
        print("  Already that model.")
        pause()
        return

    # Rebuild kiosk with same id/location/inventory/hardware but new type
    kid = kiosk.kiosk_id
    loc = kiosk.location
    pwd = kiosk.password
    inv = kiosk._inventory
    hw  = kiosk._hardware
    sensors = kiosk._sensors

    if new_type == "PharmacyKiosk":
        new_kiosk = PharmacyKiosk(kid, loc, pwd)
    elif new_type == "EmergencyKiosk":
        new_kiosk = EmergencyKiosk(kid, loc, pwd)
    else:
        new_kiosk = FoodKiosk(kid, loc, pwd)

    new_kiosk.set_hardware(hw)
    new_kiosk.set_sensors(sensors)
    new_kiosk.set_payment_processor(None)
    new_kiosk.set_inventory(inv)

    new_ki = KioskInterface(new_kiosk)
    active_kiosks[kid] = new_ki
    new_ki._save_kiosk_state()

    print(f"\n  Kiosk '{kid}' changed from {kiosk.kiosk_type} → {new_type}.")
    pause()


def admin_kiosk_menu(ki: KioskInterface, admin_id: str, active_kiosks: dict):
    """Admin view of a specific kiosk — full access."""
    kiosk = ki._kiosk
    while True:
        em = " *** EMERGENCY MODE ***" if kiosk._emergency_mode else ""
        divider(f"[ADMIN] KIOSK: {kiosk.kiosk_id} [{kiosk.kiosk_type}]{em}")

        print("\n  1. View Inventory")
        print("  2. Buy Item (as admin/test)")
        print("  3. Buy Combo (as admin/test)")
        print("  4. Refund Transaction")
        print("  5. Restock Item")
        print("  6. Run Diagnostics")
        print("  7. Kiosk Info")
        print("  8. City Monitor Events")
        print("  0. Back to Admin Menu")
        line()

        c = get_choice("  Select (0-8): ", [str(i) for i in range(9)])
        if   c == "1": do_view_inventory(ki)
        elif c == "2": do_buy_item(ki, admin_id)
        elif c == "3": do_buy_combo(ki, admin_id)
        elif c == "4": do_refund(ki, admin_id)
        elif c == "5": admin_restock({kiosk.kiosk_id: ki}, admin_id)
        elif c == "6": ki.run_diagnostics(); pause()
        elif c == "7": ki.show_kiosk_info(); pause()
        elif c == "8": do_city_monitor()
        elif c == "0": break


# ════════════════════════════════════════════════════════════
#   USER FLOWS
# ════════════════════════════════════════════════════════════
