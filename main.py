"""
File: main.py
Aura Retail OS — Interactive Simulation
Path B: Modular Hardware Platform

Flow:
  - User enters their ID once at startup
  - Main menu: Create Kiosk | Use Kiosk | Exit
  - Create: user builds kiosk step by step (items + combos + hardware + payment)
  - Use: full purchase/refund/restock/diagnostics menu
  - All data saved to persistence/data.json automatically
  - Combos: when purchased, ALL items in combo are deducted from stock
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.central_registry import CentralRegistry
from core.kiosk import Kiosk
from persistence.file_handler import FileHandler
from pattern.factory_pattern import KioskFactory
from hardware.hardware_factory import HardwareFactory
from hardware.dispenser import (
    BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
)
from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from product.product import Product
from product.bundle import ProductBundle
from product.inventory import Inventory
from kiosk.food_kiosk import FoodKiosk
from kiosk.pharmacy_kiosk import PharmacyKiosk
from kiosk.emergency_kiosk import EmergencyKiosk
from core.kiosk_interface import KioskInterface
from city_monitor.monitor import EventBus


# ── UI Helpers ────────────────────────────────────────────────────────────────

def divider(title: str):
    print(f"\n{'='*58}")
    print(f"  {title}")
    print(f"{'='*58}")

def line():
    print("-" * 58)

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


# ── Startup ───────────────────────────────────────────────────────────────────

def startup() -> str:
    """Initialize registry and get user ID."""
    registry = CentralRegistry()
    registry.initialize()

    print("\n" + "=" * 58)
    print("   AURA RETAIL OS")
    print("   Smart City Modular Kiosk Platform")
    print("   Path B: Modular Hardware Platform")
    print("=" * 58)

    user_id = ask("Enter your User ID (e.g. user_01): ", "guest_user")
    print(f"\n  Welcome, {user_id}!")
    return user_id


# ── Load saved kiosks ─────────────────────────────────────────────────────────

def load_saved_kiosks() -> dict:
    """Restore all kiosks from JSON."""
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


# ── CREATE KIOSK ──────────────────────────────────────────────────────────────

def create_kiosk_menu(active_kiosks: dict, user_id: str):
    divider("CREATE NEW VENDING MACHINE")

    # Step 1: Kiosk type
    print("\n  Kiosk types:")
    print("    1. Food Kiosk       (Metro/Campus)   — UPI")
    print("    2. Pharmacy Kiosk   (Hospital)       — Card")
    print("    3. Emergency Kiosk  (Disaster Zone)  — Wallet")
    line()
    ktype = get_choice("  Choose type (1/2/3): ", ["1", "2", "3"])
    type_map = {"1": "FoodKiosk", "2": "PharmacyKiosk", "3": "EmergencyKiosk"}
    ktype_name = type_map[ktype]

    kiosk_id = ask("  Kiosk ID (e.g. KIOSK-01): ", f"KIOSK-{len(active_kiosks)+1:02d}").upper()
    location = ask("  Location (e.g. Central Metro): ", "City Zone")

    # Step 2: Add items
    items = []
    divider("ADD ITEMS TO INVENTORY")
    print("  Add individual items to this kiosk.")
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
            print("  Invalid price/qty. Try again.")
            continue
        needs_fridge = get_choice(
            f"  Does '{name}' need refrigeration? (y/n): ", ["y", "n"]
        ) == "y"
        pid = f"P{len(items)+1:03d}"
        items.append(Product(pid, name, price, qty,
                             requires_refrigeration=needs_fridge))
        print(f"  Added: {name} | Rs.{price:.2f} | Qty:{qty}")

    # Step 3: Add combos
    combos = []
    divider("ADD COMBO OPTIONS")
    print("  Combos bundle multiple items together at a discount.")
    print("  When a combo is purchased, ALL items inside are deducted.\n")

    add_combos = get_choice("  Add combo options? (y/n): ", ["y", "n"])
    while add_combos == "y":
        combo_name = ask("  Combo name (e.g. 'Meal Deal'): ", "")
        if not combo_name:
            break
        try:
            discount = float(ask("  Discount % (e.g. 10): ", "0"))
        except ValueError:
            discount = 0.0

        # Show available items
        print("\n  Available items to add to this combo:")
        for i, item in enumerate(items, 1):
            print(f"    {i}. {item.get_name()} — Rs.{item.get_price():.2f}")
        line()

        combo_items = []
        print("  Enter item numbers to add (one at a time). Type '0' when done.")
        while True:
            try:
                choice = int(ask("  Item number (0 to finish): ", "0"))
                if choice == 0:
                    break
                if 1 <= choice <= len(items):
                    # Add the ORIGINAL product object directly — not a copy.
                    # This means bundle.confirm_sale() deducts from the real
                    # inventory item automatically. Stock is shared.
                    src = items[choice - 1]
                    combo_items.append(src)
                    print(f"  Added '{src.get_name()}' to combo.")
                else:
                    print(f"  Choose between 1 and {len(items)}")
            except ValueError:
                break

        if combo_items:
            bid = f"C{len(combos)+1:03d}"
            bundle = ProductBundle(bid, combo_name, discount_pct=discount)
            for ci in combo_items:
                bundle.add_item(ci)
            combos.append(bundle)
            print(f"  Combo '{combo_name}' created with {len(combo_items)} items "
                  f"at {discount}% discount. Stock is SHARED with individual items.")

        add_combos = get_choice("  Add another combo? (y/n): ", ["y", "n"])

    # Step 4: Hardware modules
    divider("SELECT HARDWARE MODULES")
    print("  Which optional modules does this kiosk have?\n")
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

    # Step 5: Payment method
    divider("SELECT PAYMENT METHOD")
    print("    1. UPI    — enter VPA")
    print("    2. Card   — enter token")
    print("    3. Wallet — enter wallet ID")
    line()
    pay_choice = get_choice("  Choose (1/2/3): ", ["1", "2", "3"])
    if pay_choice == "1":
        vpa = ask("  UPI VPA (e.g. kiosk@bank): ", f"{kiosk_id.lower()}@upi")
        payment = UPIAdapter(vpa=vpa)
    elif pay_choice == "2":
        token = ask("  Card token (e.g. VISA-1234): ", "CARD-0001")
        payment = CardAdapter(card_token=token)
    else:
        wid = ask("  Wallet ID: ", "WALLET-001")
        payment = DigitalWalletAdapter(wallet_id=wid)

    # Step 6: Assemble kiosk
    divider("CREATING KIOSK...")
    if ktype_name == "PharmacyKiosk":
        kiosk = PharmacyKiosk(kiosk_id, location)
    elif ktype_name == "EmergencyKiosk":
        kiosk = EmergencyKiosk(kiosk_id, location)
    else:
        kiosk = FoodKiosk(kiosk_id, location)

    hw, sensors = HardwareFactory.create_custom_hardware(kiosk_id, modules, ssid)
    kiosk.set_hardware(hw)
    kiosk.set_sensors(sensors)
    kiosk.set_payment_processor(payment)

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
    ki.show_kiosk_info()
    ki.show_inventory()
    pause()
    return ki


# ── USE KIOSK ─────────────────────────────────────────────────────────────────

def select_kiosk(active_kiosks: dict) -> KioskInterface:
    divider("SELECT VENDING MACHINE")
    print("\n  Available kiosks:")
    kids = list(active_kiosks.keys())
    for i, kid in enumerate(kids, 1):
        k = active_kiosks[kid]._kiosk
        em = " [EMERGENCY]" if k._emergency_mode else ""
        print(f"    {i}. {kid} — {k.kiosk_type} @ {k.location}{em}")
    line()
    choices = [str(i) for i in range(1, len(kids) + 1)]
    c = get_choice("  Select kiosk: ", choices)
    return active_kiosks[kids[int(c) - 1]]


def kiosk_menu(ki: KioskInterface, user_id: str):
    kiosk = ki._kiosk
    while True:
        em = " *** EMERGENCY MODE ***" if kiosk._emergency_mode else ""
        divider(f"KIOSK: {kiosk.kiosk_id} [{kiosk.kiosk_type}]{em}")

        if kiosk._emergency_mode:
            remaining = kiosk._limit_per_person if hasattr(kiosk, '_limit_per_person') else 2
            used = kiosk.get_purchase_count(user_id)
            print(f"  Your purchases: {used} | Remaining allowance: {remaining - used}")
            line()

        print("\n  1. View Inventory")
        print("  2. Buy Item")
        print("  3. Buy Combo")
        print("  4. Refund")
        print("  5. Restock (Admin)")
        print("  6. Run Diagnostics")
        print("  7. Change Payment Provider")
        print("  8. View My Transactions")
        print("  9. Kiosk Info")
        print("  0. Back to Main Menu")
        line()

        c = get_choice("  Select (0-9): ",
                       ["0","1","2","3","4","5","6","7","8","9"])
        if   c == "1": do_view_inventory(ki)
        elif c == "2": do_buy_item(ki, user_id)
        elif c == "3": do_buy_combo(ki, user_id)
        elif c == "4": do_refund(ki, user_id)
        elif c == "5": do_restock(ki)
        elif c == "6": ki.run_diagnostics(); pause()
        elif c == "7": do_change_payment(ki)
        elif c == "8": do_view_my_transactions(user_id)
        elif c == "9": ki.show_kiosk_info(); pause()
        elif c == "0": break


# ── OPERATIONS ────────────────────────────────────────────────────────────────

def do_view_inventory(ki: KioskInterface):
    divider("INVENTORY")
    ki.show_inventory()
    pause()


def do_buy_item(ki: KioskInterface, user_id: str):
    divider("BUY ITEM")
    ki.show_inventory()

    # Show low stock warning if any items are running low
    low = ki._kiosk._inventory.get_low_stock_items(threshold=5)
    if low:
        print("\n  *** LOW STOCK ALERT ***")
        for item in low:
            print(f"  *** '{item.get_name()}' — only "
                  f"{item.get_available_stock()} left! ***")
    line()

    name = ask("  Item name to buy (or 'cancel'): ", "")
    if not name or name.lower() == "cancel":
        return

    # Check item exists and show current stock
    item = ki._kiosk._inventory.find_item(name)
    if not item:
        print(f"\n  Item '{name}' not found in inventory.")
        pause()
        return

    avail = item.get_available_stock()
    if avail == 0:
        print(f"\n  Sorry, '{name}' is out of stock.")
        pause()
        return

    print(f"  Available stock: {avail} unit(s) | Price: Rs.{item.get_price():.2f} each")

    # Emergency mode — show remaining allowance
    if ki._kiosk._emergency_mode:
        used  = ki._kiosk.get_purchase_count(user_id)
        limit = getattr(ki._kiosk, '_limit_per_person',
                        getattr(ki._kiosk, '_emergency_mode', 2))
        from core.kiosk import EMERGENCY_PURCHASE_LIMIT
        remaining_allowance = EMERGENCY_PURCHASE_LIMIT - used
        print(f"  *** EMERGENCY MODE — you can buy max "
              f"{remaining_allowance} more item(s) ***")
        max_qty = min(avail, remaining_allowance)
    else:
        max_qty = avail

    # Ask quantity
    try:
        qty = int(ask(f"  How many do you want? (1-{max_qty}): ", "1"))
        qty = max(1, min(qty, max_qty))
    except ValueError:
        qty = 1

    total = item.get_price() * qty
    print(f"\n  Order summary: {qty}x {name} = Rs.{total:.2f}")
    confirm = get_choice("  Confirm purchase? (y/n): ", ["y", "n"])
    if confirm == "n":
        print("  Purchase cancelled.")
        pause()
        return

    result = ki.purchase_item(name, user_id, quantity=qty)
    print(f"\n  {'Purchase successful!' if result else 'Purchase failed.'}")
    pause()


def do_buy_combo(ki: KioskInterface, user_id: str):
    """
    Buy a combo — all items inside are deducted from stock atomically.
    """
    divider("BUY COMBO")
    inv = ki._kiosk._inventory

    # Show only bundles
    bundles = [item for item in inv.get_all_items()
               if isinstance(item, ProductBundle)]

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
        print(f"\n  '{bundle.get_name()}' is not available (check stock).")
        pause()
        return

    if not ki._kiosk.can_user_purchase(user_id):
        print(f"\n  Emergency limit reached. Cannot purchase.")
        pause()
        return

    # Use purchase_item which internally uses PurchaseCommand
    # Bundles are in inventory so purchase_item works for them too
    result = ki.purchase_item(bundle.get_name(), user_id)
    if result:
        print(f"\n  Combo '{bundle.get_name()}' purchased!")
        print(f"  All {len(bundle._items)} items deducted from stock.")
    else:
        print(f"\n  Combo purchase failed.")
    pause()


def do_refund(ki: KioskInterface, user_id: str):
    divider("REFUND")

    # Show only THIS user's successful purchases
    all_txns = FileHandler.load_transactions()
    my_txns = [t for t in all_txns
               if t.get("user_id") == user_id
               and t.get("kiosk_id") == ki._kiosk.kiosk_id
               and t.get("type") == "PURCHASE"
               and t.get("status") == "SUCCESS"]

    if not my_txns:
        print(f"\n  No refundable purchases found for user '{user_id}'.")
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

    # Verify it belongs to this user before proceeding
    valid = any(t["txn_id"] == txn_id for t in my_txns)
    if not valid:
        print(f"\n  Transaction '{txn_id}' not found in your purchases.")
        pause()
        return

    result = ki.refund_transaction(txn_id, user_id)
    print(f"\n  {'Refund successful!' if result else 'Refund failed.'}")
    pause()


def do_restock(ki: KioskInterface):
    divider("RESTOCK (Admin)")
    admin_id = ask("  Admin ID: ", "admin")
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


def do_change_payment(ki: KioskInterface):
    divider("CHANGE PAYMENT PROVIDER")
    print("    1. UPI")
    print("    2. Card")
    print("    3. Wallet")
    line()
    c = get_choice("  Choose (1/2/3): ", ["1", "2", "3"])
    if c == "1":
        vpa = ask("  UPI VPA: ", "kiosk@upi")
        ki._kiosk.set_payment_processor(UPIAdapter(vpa=vpa))
    elif c == "2":
        token = ask("  Card token: ", "CARD-0001")
        ki._kiosk.set_payment_processor(CardAdapter(card_token=token))
    else:
        wid = ask("  Wallet ID: ", "WALLET-001")
        ki._kiosk.set_payment_processor(DigitalWalletAdapter(wallet_id=wid))
    print("  Payment provider updated.")
    ki._save_kiosk_state()
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


# ── MAIN MENU ─────────────────────────────────────────────────────────────────

def main():
    user_id = startup()
    active_kiosks = load_saved_kiosks()

    while True:
        divider("MAIN MENU")
        print(f"\n  Logged in as: {user_id}")
        print(f"  Active kiosks: {len(active_kiosks)}")
        print("\n  1. Create New Vending Machine")
        print("  2. Use Existing Vending Machine")
        print("  3. City Monitor Events")
        print("  4. System Registry Summary")
        print("  5. Exit")
        line()

        c = get_choice("  Select (1-5): ", ["1", "2", "3", "4", "5"])

        if c == "1":
            create_kiosk_menu(active_kiosks, user_id)

        elif c == "2":
            if not active_kiosks:
                print("\n  No kiosks found. Please create one first.")
                pause()
            else:
                ki = select_kiosk(active_kiosks)
                kiosk_menu(ki, user_id)

        elif c == "3":
            do_city_monitor()

        elif c == "4":
            do_registry_summary()

        elif c == "5":
            print("\n  Saving all data...")
            for kid, ki in active_kiosks.items():
                ki._save_kiosk_state()
            print("  All kiosks saved. Goodbye!\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
