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
    """
    Initializes the system registry and handles the initial role-based
    authentication and routing for the entire platform.
    Returns a tuple of (role_string, user_identifier).
    """
    # 1. Boot up core singletons
    system_registry = CentralRegistry()
    system_registry.initialize()

    # 2. Display Platform Header
    header_bar = "=" * 60
    os_name = "   AURA RETAIL OS"
    os_subtitle = "   Smart City Modular Kiosk Platform"
    
    print(f"\n{header_bar}")
    print(os_name)
    print(os_subtitle)
    print(header_bar)

    # 3. Prompt for Role Selection
    print("\n  Who are you?")
    print("    1. User   — Browse & purchase from vending machines")
    print("    2. Admin  — Full system management (password required)")
    line()
    
    valid_roles = ["1", "2"]
    selected_role_id = get_choice("  Select (1/2): ", valid_roles)
    
    is_admin_selected = (selected_role_id == "2")

    # 4. Handle Administrator Authentication Flow
    if is_admin_selected:
        max_login_attempts = 3
        login_successful = False
        
        for current_attempt_index in range(max_login_attempts):
            entered_password = input("  Enter admin password: ").strip()
            
            if entered_password == ADMIN_PASSWORD:
                login_successful = True
                print("\n  Admin access granted.")
                
                # Fetch Admin Identity
                provided_admin_id = ask("  Admin ID (e.g. admin_01): ", "admin_01")
                print(f"\n  Welcome, Admin {provided_admin_id}!")
                
                return "admin", provided_admin_id
            else:
                remaining_attempts = (max_login_attempts - 1) - current_attempt_index
                if remaining_attempts > 0:
                    print(f"  Wrong password. {remaining_attempts} attempt(s) left.")
                else:
                    print("  Too many failed attempts. Switching to User mode.")
                    # Break out to fallback to standard user flow
                    break

    # 5. Handle Standard User Onboarding Flow
    prompt_msg = "Enter your User ID (e.g. user_01): "
    default_user = "guest_user"
    
    provided_user_id = ask(prompt_msg, default_user)
    print(f"\n  Welcome, {provided_user_id}!")
    
    return "user", provided_user_id


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


def user_main_menu(active_kiosks: dict, user_id: str):
    """User menu — vending machine operations only."""
    while True:
        divider(f"VENDING MACHINE — Welcome, {user_id}")
        print(f"\n  Available kiosks: {len(active_kiosks)}")

        if not active_kiosks:
            print("\n  No vending machines available. Please contact an admin.")
            pause()
            return

        print("\n  1. Browse & Buy from Vending Machine")
        print("  2. View My Transactions")
        print("  3. Exit")
        line()

        c = get_choice("  Select (1-3): ", ["1", "2", "3"])

        if c == "1":
            ki = select_kiosk(active_kiosks)
            user_kiosk_menu(ki, user_id)
        elif c == "2":
            do_view_my_transactions(user_id)
        elif c == "3":
            print("\n  Goodbye!\n")
            sys.exit(0)


def user_kiosk_menu(ki: KioskInterface, user_id: str):
    """User-facing kiosk operations."""
    kiosk = ki._kiosk
    while True:
        em = " *** EMERGENCY MODE ***" if kiosk._emergency_mode else ""
        divider(f"KIOSK: {kiosk.kiosk_id} [{kiosk.kiosk_type}]{em}")

        if kiosk._emergency_mode:
            from core.kiosk import EMERGENCY_PURCHASE_LIMIT
            used = kiosk.get_purchase_count(user_id)
            print(f"  Your purchases: {used} | Remaining allowance: {EMERGENCY_PURCHASE_LIMIT - used}")
            line()

        print("\n  1. View Inventory")
        print("  2. Buy Item")
        print("  3. Buy Combo")
        print("  4. Refund")
        print("  5. View My Transactions")
        print("  6. Kiosk Info")
        print("  0. Back")
        line()

        c = get_choice("  Select (0-6): ", ["0","1","2","3","4","5","6"])
        if   c == "1": do_view_inventory(ki)
        elif c == "2": do_buy_item(ki, user_id)
        elif c == "3": do_buy_combo(ki, user_id)
        elif c == "4": do_refund(ki, user_id)
        elif c == "5": do_view_my_transactions(user_id)
        elif c == "6": ki.show_kiosk_info(); pause()
        elif c == "0": break


# ════════════════════════════════════════════════════════════
#   SHARED OPERATIONS
# ════════════════════════════════════════════════════════════

def select_kiosk(active_kiosks: dict) -> KioskInterface:
    divider("SELECT VENDING MACHINE")
    kids = list(active_kiosks.keys())
    for i, kid in enumerate(kids, 1):
        k = active_kiosks[kid]._kiosk
        em = " [EMERGENCY]" if k._emergency_mode else ""
        print(f"    {i}. {kid} — {k.kiosk_type} @ {k.location}{em}")
    line()
    choices = [str(i) for i in range(1, len(kids) + 1)]
    c = get_choice("  Select kiosk: ", choices)
    return active_kiosks[kids[int(c) - 1]]

def _check_kiosk_password(ki: KioskInterface) -> bool:
    pwd = input(f"  Enter password for kiosk '{ki._kiosk.kiosk_id}': ").strip()
    if pwd == ki._kiosk.password:
        return True
    print("  Incorrect password.")
    pause()
    return False


def do_view_inventory(ki: KioskInterface):
    divider("INVENTORY")
    ki.show_inventory()
    pause()


def do_buy_item(ki: KioskInterface, user_id: str):
    """
    Initiates and processes the purchase flow for a single item from the Kiosk.
    Handles inventory checks, emergency mode rationing, and payment selection.
    """
    # 1. Display Header and Current Inventory
    divider("BUY ITEM")
    ki.show_inventory()

    # 2. Check for low stock thresholds and display warnings
    critical_stock_threshold = 5
    low_stock_items = ki._kiosk._inventory.get_low_stock_items(threshold=critical_stock_threshold)
    
    if low_stock_items:
        print("\n  *** LOW STOCK ALERT ***")
        for low_item in low_stock_items:
            item_name = low_item.get_name()
            remaining = low_item.get_available_stock()
            print(f"  *** '{item_name}' — only {remaining} left! ***")
            
    line()

    # 3. Prompt User for Target Item
    target_item_name = ask("  Item name to buy (or 'cancel'): ", "")
    
    # 4. Handle Cancellation
    is_cancelled = (not target_item_name or target_item_name.lower() == "cancel")
    if is_cancelled:
        return

    # 5. Validate Item Existence
    selected_product_entity = ki._kiosk._inventory.find_item(target_item_name)
    if selected_product_entity is None:
        print(f"\n  Item '{target_item_name}' not found in this kiosk.")
        pause()
        return

    # 6. Validate Item Physical Availability
    available_stock_count = selected_product_entity.get_available_stock()
    if available_stock_count == 0:
        print(f"\n  Sorry, '{target_item_name}' is currently out of stock.")
        pause()
        return

    # 7. Display Item Pricing Details
    unit_price = selected_product_entity.get_price()
    print(f"  Available: {available_stock_count} unit(s) | Price: Rs.{unit_price:.2f} each")

    # 8. Evaluate Emergency Mode Purchase Allowances
    is_emergency_mode_active = ki._kiosk._emergency_mode
    max_purchasable_quantity = available_stock_count
    
    if is_emergency_mode_active:
        from core.kiosk import EMERGENCY_PURCHASE_LIMIT
        historical_user_purchase_count = ki._kiosk.get_purchase_count(user_id)
        
        remaining_allowance_for_user = EMERGENCY_PURCHASE_LIMIT - historical_user_purchase_count
        print(f"  *** EMERGENCY MODE — you can buy max {remaining_allowance_for_user} more item(s) ***")
        
        # Clamp maximum quantity to either physical stock or user allowance
        max_purchasable_quantity = min(available_stock_count, remaining_allowance_for_user)

    # 9. Prompt User for Quantity
    requested_quantity = 1
    try:
        raw_quantity_input = ask(f"  How many? (1-{max_purchasable_quantity}): ", "1")
        parsed_quantity = int(raw_quantity_input)
        
        # Enforce bounds
        bounded_quantity = max(1, min(parsed_quantity, max_purchasable_quantity))
        requested_quantity = bounded_quantity
    except ValueError:
        # Fallback to default safely
        requested_quantity = 1

    # 10. Calculate and Display Order Total
    calculated_total_price = unit_price * requested_quantity
    print(f"\n  Order: {requested_quantity}x {target_item_name} = Rs.{calculated_total_price:.2f}")

    # 11. Interactive Payment Selection Phase
    selected_payment_processor = PaymentSelector.select_payment()
    if selected_payment_processor is None:
        print("  Purchase cancelled during payment selection.")
        pause()
        return

    # Inject the selected payment strategy into the Kiosk instance
    ki._kiosk.set_payment_processor(selected_payment_processor)

    # 12. Final Confirmation
    valid_confirmation_inputs = ["y", "n"]
    user_confirmation = get_choice("  Confirm purchase? (y/n): ", valid_confirmation_inputs)
    
    if user_confirmation == "n":
        print("  Purchase cancelled by user.")
        pause()
        return

    # 13. Execute Transaction
    transaction_successful = ki.purchase_item(target_item_name, user_id, quantity=requested_quantity)
    
    if transaction_successful:
        print("\n  Purchase successful!")
    else:
        print("\n  Purchase failed.")
        
    pause()


def do_buy_combo(ki: KioskInterface, user_id: str):
    """Buy a combo — user selects payment at purchase time."""
    divider("BUY COMBO")
    inv = ki._kiosk._inventory

    bundles = [item for item in inv.get_all_items() if isinstance(item, ProductBundle)]
    if not bundles:
        print("\n  No combos available in this kiosk.")
        pause()
        return

    print("\n  Available Combos:")
    for i, b in enumerate(bundles, 1):
        print(f"    {i}. ", end="")
        b.display(indent=0)
    line()

    choices = [str(i) for i in range(1, len(bundles) + 1)]
    choices.append("0")
    c = get_choice("  Select combo (0 to cancel): ", choices)
    if c == "0":
        return

    bundle = bundles[int(c) - 1]

    if not bundle.is_available():
        print(f"\n  '{bundle.get_name()}' is not available.")
        pause()
        return

    if not ki._kiosk.can_user_purchase(user_id):
        print(f"\n  Emergency limit reached.")
        pause()
        return

    # ── PAYMENT SELECTION ────────────────────────────────────────────
    payment = PaymentSelector.select_payment()
    if payment is None:
        print("  Purchase cancelled.")
        pause()
        return

    ki._kiosk.set_payment_processor(payment)

    result = ki.purchase_item(bundle.get_name(), user_id)
    if result:
        print(f"\n  Combo '{bundle.get_name()}' purchased!")
    else:
        print(f"\n  Combo purchase failed.")
    pause()


def do_refund(ki: KioskInterface, user_id: str):
    divider("REFUND")
    all_txns = FileHandler.load_transactions()
    my_txns = [t for t in all_txns
               if t.get("user_id") == user_id
               and t.get("kiosk_id") == ki._kiosk.kiosk_id
               and t.get("type") == "PURCHASE"
               and t.get("status") == "SUCCESS"]

    if not my_txns:
        print(f"\n  No refundable purchases found for '{user_id}'.")
        pause()
        return

    print(f"\n  Your purchases at {ki._kiosk.kiosk_id}:")
    for i, t in enumerate(my_txns[-8:], 1):
        print(f"    {i}. [{t['txn_id']}] {t['item']:<22} "
              f"Rs.{t['amount']:>7.2f}  ({t['timestamp'][:10]})")
    line()

    txn_id = ask("  Enter Transaction ID to refund (or 'cancel'): ", "")
    if not txn_id or txn_id.lower() == "cancel":
        return

    valid = any(t["txn_id"] == txn_id for t in my_txns)
    if not valid:
        print(f"\n  Transaction '{txn_id}' not found in your purchases.")
        pause()
        return

    result = ki.refund_transaction(txn_id, user_id)
    print(f"\n  {'Refund successful!' if result else 'Refund failed.'}")
    pause()


def do_view_my_transactions(user_id: str):
    divider(f"MY TRANSACTIONS — {user_id}")
    all_txns = FileHandler.load_transactions()
    my_txns = [t for t in all_txns if t.get("user_id") == user_id]

    if not my_txns:
        print(f"\n  No transactions found for '{user_id}'.")
    else:
        print(f"\n  {'Type':<10} {'Item':<22} {'Amount':>8}  "
              f"{'Status':<12} {'Date'}")
        line()
        for t in my_txns[-15:]:
            print(f"  {t.get('type','?'):<10} {t.get('item','?'):<22} "
                  f"Rs.{t.get('amount',0):>6.2f}  "
                  f"{t.get('status','?'):<12} "
                  f"{t.get('timestamp','')[:10]}")
        line()
        print(f"  Total: {len(my_txns)} record(s)")
    pause()


def do_city_monitor():
    divider("CITY MONITORING CENTER")
    bus = EventBus()
    monitor = bus.get_city_monitor()
    monitor.display_log()
    pause()


def do_registry_summary():
    divider("SYSTEM REGISTRY SUMMARY")
    CentralRegistry().display_summary()
    pause()


# ── Helper: collect items interactively ───────────────────────────────────────

def _collect_items() -> list:
    items = []
    divider("ADD ITEMS TO INVENTORY")
    print("  Type 'done' as item name when finished.\n")
    while True:
        name = ask("  Item name (or 'done'): ", "")
        if name.lower() == "done" or name == "":
            if not items:
                print("  At least one item is required.")
                continue
            break
        try:
            price = float(ask(f"  Price for '{name}' (Rs.): ", "0"))
            qty   = int(ask(f"  Quantity for '{name}': ", "10"))
        except ValueError:
            print("  Invalid price/qty.")
            continue
        needs_fridge = get_choice(
            f"  Needs refrigeration? (y/n): ", ["y", "n"]
        ) == "y"
        pid = f"P{len(items)+1:03d}"
        items.append(Product(pid, name, price, qty,
                             requires_refrigeration=needs_fridge))
        print(f"  Added: {name} | Rs.{price:.2f} | Qty:{qty}")
    return items


def _collect_combos(items: list) -> list:
    combos = []
    divider("ADD COMBO OPTIONS")
    print("  Combos bundle multiple items at a discount.\n")
    add_combos = get_choice("  Add combo options? (y/n): ", ["y", "n"])
    while add_combos == "y":
        combo_name = ask("  Combo name: ", "")
        if not combo_name:
            break
        try:
            discount = float(ask("  Discount % (e.g. 10): ", "0"))
        except ValueError:
            discount = 0.0

        print("\n  Available items:")
        for i, item in enumerate(items, 1):
            print(f"    {i}. {item.get_name()} — Rs.{item.get_price():.2f}")
        line()

        combo_items = []
        print("  Enter item numbers. Type '0' when done.")
        while True:
            try:
                choice = int(ask("  Item number (0 to finish): ", "0"))
                if choice == 0:
                    break
                if 1 <= choice <= len(items):
                    combo_items.append(items[choice - 1])
                    print(f"  Added '{items[choice-1].get_name()}'.")
            except ValueError:
                break

        if combo_items:
            bid = f"C{len(combos)+1:03d}"
            bundle = ProductBundle(bid, combo_name, discount_pct=discount)
            for ci in combo_items:
                bundle.add_item(ci)
            combos.append(bundle)
            print(f"  Combo '{combo_name}' created with {len(combo_items)} items.")

        add_combos = get_choice("  Add another combo? (y/n): ", ["y", "n"])
    return combos


def _collect_hardware(kiosk_id: str):
    divider("SELECT HARDWARE MODULES")
    modules = []
    if get_choice("  Refrigeration module? (y/n): ", ["y", "n"]) == "y":
        modules.append("refrigeration")
    if get_choice("  Solar power module?   (y/n): ", ["y", "n"]) == "y":
        modules.append("solar_power")
    if get_choice("  Network module?       (y/n): ", ["y", "n"]) == "y":
        modules.append("network")
    ssid = "CityNet"
    if "network" in modules:
        ssid = ask("  Network SSID: ", "CityNet")
    hw, sensors = HardwareFactory.create_custom_hardware(kiosk_id, modules, ssid)
    return hw, sensors, modules


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    role, user_id = startup()
    active_kiosks = load_saved_kiosks()

    if role == "admin":
        admin_main_menu(active_kiosks, user_id)
    else:
        user_main_menu(active_kiosks, user_id)


if __name__ == "__main__":
    main()
