"""
DESIGN PATTERN: Facade
File: core/kiosk_interface.py
Purpose: Simplified public API for all kiosk operations.
         External code never touches subsystems directly.
         All operations are routed through Command objects internally.
         FACADE hides: inventory, payment, hardware, commands, persistence.
"""

from core.kiosk import Kiosk
from commands.command import CommandHistory
from commands.purchase_command import PurchaseCommand
from commands.refund_command import RefundCommand
from commands.restock_command import RestockCommand
from persistence.file_handler import FileHandler


class KioskInterface:
    """
    FACADE: Single entry point for all kiosk operations.
    Internally uses Command pattern for atomic execution and audit logging.
    """

    def __init__(self, kiosk: Kiosk):
        self._kiosk  = kiosk
        self._history = CommandHistory()

    # ── Public Facade API ─────────────────────────────────────────────────────

    def purchase_item(self, item_name: str, user_id: str,
                      quantity: int = 1) -> bool:
        print(f"\n[KioskInterface] Purchase: {quantity}x '{item_name}' | User: {user_id}")

        if not self._kiosk.is_operational():
            print(f"  ERROR: Kiosk is {self._kiosk.get_mode()} — cannot purchase.")
            return False

        if self._kiosk._payment_processor is None:
            print("  ERROR: No payment method set. User must select payment first.")
            return False

        item = self._kiosk._inventory.find_item(item_name)
        if not item:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        if item.get_available_stock() < quantity:
            print(f"  ERROR: Only {item.get_available_stock()} unit(s) available "
                  f"but {quantity} requested.")
            return False

        success_count = 0
        for i in range(quantity):
            if not self._kiosk.can_user_purchase(user_id):
                print(f"  STOPPED: Emergency limit reached after {success_count} item(s).")
                break

            cmd = PurchaseCommand(
                kiosk_id=self._kiosk.kiosk_id,
                user_id=user_id,
                item=item,
                payment_processor=self._kiosk._payment_processor,
                pricing_context=self._kiosk._pricing,
                kiosk_ref=self._kiosk,
            )

            ok = cmd.execute()
            self._history.record(cmd)

            if ok:
                success_count += 1
                self._kiosk.record_purchase(user_id)
                self._kiosk.check_and_activate_emergency()
            else:
                print(f"  STOPPED at unit {i+1} — purchase failed.")
                break

        if success_count > 0:
            self._save_kiosk_state()
            remaining = item.get_available_stock()
            if remaining <= 5:
                print(f"\n  *** WARNING: Only {remaining} unit(s) of "
                      f"'{item_name}' left in stock! ***")

        if success_count > 0 and success_count < quantity:
            print(f"  Partial success: {success_count}/{quantity} purchased.")

        return success_count > 0

    def refund_transaction(self, txn_id: str, user_id: str) -> bool:
        print(f"\n[KioskInterface] Refund txn: {txn_id} | User: {user_id}")

        txns = FileHandler.load_transactions()
        txn  = next((t for t in txns
                     if t.get("txn_id") == txn_id
                     and t.get("user_id") == user_id), None)

        item = None
        if txn:
            item = self._kiosk._inventory.find_item(txn.get("item", ""))

        cmd = RefundCommand(
            kiosk_id=self._kiosk.kiosk_id,
            user_id=user_id,
            txn_id=txn_id,
            item=item,
            payment_processor=self._kiosk._payment_processor,
        )

        success = cmd.execute()
        self._history.record(cmd)

        if success:
            self._save_kiosk_state()

        return success

    def restock_inventory(self, item_name: str, quantity: int,
                          admin_id: str = "admin") -> bool:
        print(f"\n[KioskInterface] Restock: {quantity}x '{item_name}'")

        item = self._kiosk._inventory.find_item(item_name)
        if not item:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        cmd = RestockCommand(
            kiosk_id=self._kiosk.kiosk_id,
            user_id=admin_id,
            item=item,
            quantity=quantity,
        )

        success = cmd.execute()
        self._history.record(cmd)

        if success:
            # Deactivate emergency mode if all stock is back above threshold
            if (self._kiosk._emergency_mode and
                    not self._kiosk._inventory.get_low_stock_items(5)):
                self._kiosk.deactivate_emergency_mode()
            self._save_kiosk_state()

        return success

    def run_diagnostics(self) -> dict:
        print(f"\n[KioskInterface] Diagnostics: {self._kiosk.kiosk_id}")
        hw = self._kiosk._hardware
        if not hw:
            print("  No hardware attached.")
            return {}

        print(f"  Status      : {hw.get_status()}")
        print(f"  Capabilities: {hw.get_capabilities()}")
        print(f"  Healthy     : {hw.is_healthy()}")

        diag = hw.run_diagnostics()
        if self._kiosk._sensors:
            diag["sensors"] = self._kiosk._sensors.run_diagnostics()
            self._kiosk._sensors.display()

        for k, v in diag.items():
            if k != "kiosk_id":
                print(f"  {k}: {v}")
        return diag

    def show_inventory(self):
        print(f"\n[KioskInterface] Inventory — {self._kiosk.kiosk_id}:")
        self._kiosk._inventory.display()

    def show_kiosk_info(self):
        self._kiosk.display_info()

    def get_user_transactions(self, user_id: str) -> list:
        return [t for t in FileHandler.load_transactions()
                if t.get("user_id") == user_id]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _save_kiosk_state(self):
        """Persist kiosk state to JSON after every operation."""
        FileHandler.save_kiosk(
            self._kiosk.kiosk_id,
            self._kiosk.to_dict()
        )
