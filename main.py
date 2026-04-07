"""
File: main.py
Aura Retail OS — Subtask 2 Simulation
Path B: Modular Hardware Platform

Patterns demonstrated:
  1. Adapter   — Payment system integration (UPI, Card, Wallet)
  2. Decorator — Optional hardware modules (fridge, solar, network)
  3. Composite — Nested product bundles
  4. Factory   — KioskFactory creates fully configured kiosks
  5. Singleton — CentralRegistry global state
  6. Facade    — KioskInterface simplified API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patterns.factory_pattern import KioskFactory
from hardware.dispenser import (
    BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
)
from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from inventory.product import Product
from inventory.bundle import ProductBundle
from core.central_registry import CentralRegistry


def divider(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1: Adapter Pattern — Payment Provider Integration
# ─────────────────────────────────────────────────────────────────────────────
def scenario_adapter_pattern():
    divider("SCENARIO 1: Adapter Pattern — Payment Integration")

    print("\n--- Metro Food Kiosk using UPI ---")
    food_kiosk = KioskFactory.create_food_kiosk("KIOSK-METRO-01", "Central Metro Station")
    food_kiosk.show_inventory()
    food_kiosk.purchase_item("Water Bottle", "user_arun")
    food_kiosk.purchase_item("Sandwich", "user_priya")

    print("\n--- Hospital Pharmacy Kiosk using Card ---")
    pharmacy_kiosk = KioskFactory.create_pharmacy_kiosk("KIOSK-HOSP-01", "City Hospital")
    pharmacy_kiosk.show_inventory()
    pharmacy_kiosk.purchase_item("Paracetamol 500mg", "patient_001")

    print("\n--- Switching payment provider at runtime (no kiosk code change) ---")
    # The kiosk interface stays the same — only the adapter changes
    food_kiosk._kiosk.set_payment_processor(CardAdapter(card_token="VISA-9999"))
    food_kiosk.purchase_item("Chips", "user_ravi")
    print("  [NOTE] Payment switched from UPI to Card — kiosk logic unchanged.")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2: Decorator Pattern — Dynamic Hardware Modules
# ─────────────────────────────────────────────────────────────────────────────
def scenario_decorator_pattern():
    divider("SCENARIO 2: Decorator Pattern — Hardware Module Stacking")

    kiosk_id = "KIOSK-UNI-01"

    print("\n--- Step 1: Base hardware only ---")
    base = BaseDispenser(kiosk_id)
    print(f"  Status      : {base.get_status()}")
    print(f"  Capabilities: {base.get_capabilities()}")

    print("\n--- Step 2: Add refrigeration module ---")
    with_fridge = RefrigerationModule(base, target_temp_c=4.0)
    print(f"  Status      : {with_fridge.get_status()}")
    print(f"  Capabilities: {with_fridge.get_capabilities()}")

    print("\n--- Step 3: Add solar module on top ---")
    with_solar = SolarModule(with_fridge)
    print(f"  Status      : {with_solar.get_status()}")
    print(f"  Capabilities: {with_solar.get_capabilities()}")

    print("\n--- Step 4: Add network module on top ---")
    full_hw = NetworkModule(with_solar, ssid="UniversityNet")
    print(f"  Status      : {full_hw.get_status()}")
    print(f"  Capabilities: {full_hw.get_capabilities()}")

    print("\n--- Full diagnostics ---")
    diag = full_hw.run_diagnostics()
    for key, val in diag.items():
        print(f"  {key}: {val}")

    print("\n  [NOTE] Each module was added WITHOUT modifying BaseDispenser.")
    print("  [NOTE] Hardware can be replaced at runtime without changing kiosk logic.")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3: Composite Pattern — Nested Product Bundles
# ─────────────────────────────────────────────────────────────────────────────
def scenario_composite_pattern():
    divider("SCENARIO 3: Composite Pattern — Nested Bundles")

    # Individual products
    bandage = Product("P010", "Bandage", 15.0, stock=100)
    antiseptic = Product("P011", "Antiseptic", 40.0, stock=50)
    torch = Product("P012", "Torch", 80.0, stock=30)
    ration = Product("P013", "Ration Pack", 120.0, stock=20)

    # Bundle containing products
    basic_kit = ProductBundle("B100", "Basic Supply Kit", discount_pct=5)
    basic_kit.add_item(bandage)
    basic_kit.add_item(antiseptic)

    # Bundle containing another bundle (nested composite)
    emergency_kit = ProductBundle("B200", "Emergency Relief Kit", discount_pct=15)
    emergency_kit.add_item(basic_kit)       # nested bundle
    emergency_kit.add_item(torch)
    emergency_kit.add_item(ration)

    print("\nInventory tree (recursive display):")
    emergency_kit.display()

    print(f"\n  Emergency Kit Price  : Rs.{emergency_kit.get_price():.2f}")
    print(f"  Available Stock      : {emergency_kit.get_available_stock()}")
    print(f"  Is Available         : {emergency_kit.is_available()}")
    print("\n  [NOTE] price and stock resolve recursively through the bundle tree.")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4: Factory Pattern — Kiosk Creation
# ─────────────────────────────────────────────────────────────────────────────
def scenario_factory_pattern():
    divider("SCENARIO 4: Factory Pattern — Kiosk Creation")

    print("\n--- Factory creates Emergency Kiosk with all components wired ---")
    emergency_kiosk = KioskFactory.create_emergency_kiosk(
        "KIOSK-RELIEF-01", "Disaster Zone A"
    )
    emergency_kiosk.show_inventory()
    emergency_kiosk.run_diagnostics()
    emergency_kiosk.purchase_item("Ration Pack", "household_042")
    emergency_kiosk.purchase_item("Water Pouch", "household_042")

    print("\n  [NOTE] Caller used one factory method — hardware, payment,")
    print("  and inventory were all configured automatically.")


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def show_registry():
    divider("CENTRAL REGISTRY — Transaction Log & Persistence")
    registry = CentralRegistry()
    registry.display_summary()
    registry.save_to_file("persistence/data.json")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AURA RETAIL OS — Subtask 2 Simulation")
    print("  Path B: Modular Hardware Platform")
    print("=" * 60)

    scenario_adapter_pattern()
    scenario_decorator_pattern()
    scenario_composite_pattern()
    scenario_factory_pattern()
    show_registry()

    print("\n[Simulation complete]")
