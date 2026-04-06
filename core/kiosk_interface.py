"""
DESIGN PATTERN: Facade
File: core/kiosk_interface.py
Purpose: Exposes a simplified API to external systems.
         Internally coordinates kiosk, payment, hardware, and inventory.
"""

import uuid
import datetime
from core.kiosk import Kiosk
from core.central_registry import CentralRegistry


class KioskInterface:
    """
    FACADE: Hides all internal subsystem complexity.
    External code only calls: purchaseItem, refundTransaction,
    runDiagnostics, restockInventory.
    """

    def __init__(self, kiosk: Kiosk):
        self._kiosk = kiosk
        self._registry = CentralRegistry()

    # ── Public API (Facade methods) ───────────────────────────────────────────

    def purchase_item(self, item_name: str, user_id: str) -> bool:
        print(f"\n[KioskInterface] Purchase: '{item_name}' | User: {user_id}")

        if not self._kiosk.is_operational():
            print(f"  ERROR: Kiosk is in {self._kiosk.get_mode()} mode. Cannot process purchase.")
            return False

        item = self._find_item(item_name)
        if item is None:
            print(f"  ERROR: Item '{item_name}' not found in inventory.")
            return False

        if not item.is_available():
            print(f"  ERROR: '{item_name}' is out of stock.")
            return False

        price = item.get_price()
        processor = self._kiosk._payment_processor

        if processor is None:
            print("  ERROR: No payment processor configured.")
            return False

        success = processor.process_payment(price, user_id)

        if success:
            item.confirm_sale()
            txn = {
                "txn_id": str(uuid.uuid4())[:8],
                "kiosk_id": self._kiosk.kiosk_id,
                "item": item_name,
                "amount": price,
                "user": user_id,
                "provider": processor.get_provider_name(),
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "COMPLETED",
            }
            self._registry.log_transaction(txn)
            print(f"  SUCCESS: '{item_name}' purchased for Rs.{price:.2f} "
                  f"via {processor.get_provider_name()}")
            return True
        else:
            print("  FAILED: Payment was unsuccessful.")
            return False

    def refund_transaction(self, txn_id: str, amount: float = 0.0) -> bool:
        print(f"\n[KioskInterface] Refund for txn: {txn_id}")
        processor = self._kiosk._payment_processor
        if processor is None:
            print("  ERROR: No payment processor configured.")
            return False
        result = processor.refund_payment(txn_id, amount)
        print(f"  Refund {'SUCCESS' if result else 'FAILED'}")
        return result

    def run_diagnostics(self) -> dict:
        print(f"\n[KioskInterface] Running diagnostics on {self._kiosk.kiosk_id}...")
        hw = self._kiosk._hardware
        if hw is None:
            print("  WARNING: No hardware module attached.")
            return {}
        diag = hw.run_diagnostics()
        print(f"  Status      : {hw.get_status()}")
        print(f"  Capabilities: {hw.get_capabilities()}")
        return diag

    def restock_inventory(self, item_name: str, quantity: int):
        print(f"\n[KioskInterface] Restocking {quantity}x '{item_name}'")
        item = self._find_item(item_name)
        if item and hasattr(item, '_stock'):
            item._stock += quantity
            print(f"  New stock level: {item.get_available_stock()}")
        else:
            print(f"  ERROR: Item '{item_name}' not found or not restockable.")

    def show_inventory(self):
        print(f"\n[KioskInterface] Inventory for {self._kiosk.kiosk_id}:")
        for item in self._kiosk._inventory:
            item.display(indent=1)

    # ── Internal helper ───────────────────────────────────────────────────────

    def _find_item(self, name: str):
        for item in self._kiosk._inventory:
            if item.get_name().lower() == name.lower():
                return item
        return None
