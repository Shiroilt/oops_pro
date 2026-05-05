"""
DESIGN PATTERN: Facade
File: core/kiosk_interface.py
Purpose: Acts as a single entry point for all kiosk operations.

         Clients interact only with this class.
         Internally uses Command pattern for execution and logging.

         Hides complexity of:
         - Inventory
         - Payment
         - Hardware
         - Persistence
"""

from core.kiosk import Kiosk
from commands.command import CommandHistory
from commands.purchase_command import PurchaseCommand
from commands.refund_command import RefundCommand
from commands.restock_command import RestockCommand
from persistence.file_handler import FileHandler


class KioskInterface:
    """
    Facade layer for kiosk system.
    Simplifies interaction and ensures controlled execution flow.
    """

    def __init__(self, kiosk: Kiosk):
        self._kiosk_obj   = kiosk
        self._history_log = CommandHistory()

    # ── Public API ────────────────────────────────────────────────────────────

    def purchase_item(self, item_name: str, user_id: str, quantity: int = 1) -> bool:

        print(f"\n[KioskInterface] Purchase: {quantity}x '{item_name}' | User: {user_id}")

        if not self._kiosk_obj.is_operational():
            print(f"  ERROR: Kiosk is {self._kiosk_obj.get_mode()} — cannot purchase.")
            return False

        if self._kiosk_obj._payment_processor is None:
            print("  ERROR: No payment method configured.")
            return False

        product = self._kiosk_obj._inventory.find_item(item_name)
        if not product:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        if product.get_available_stock() < quantity:
            print(f"  ERROR: Only {product.get_available_stock()} unit(s) available "
                  f"but {quantity} requested.")
            return False

        success_count = 0

        for i in range(quantity):

            if not self._kiosk_obj.can_user_purchase(user_id):
                print(f"  STOPPED: Limit reached after {success_count} item(s).")
                break

            command = PurchaseCommand(
                kiosk_id=self._kiosk_obj.kiosk_id,
                user_id=user_id,
                item=product,
                payment_processor=self._kiosk_obj._payment_processor,
                pricing_context=self._kiosk_obj._pricing,
                kiosk_ref=self._kiosk_obj,
            )

            result = command.execute()
            self._history_log.record(command)

            if result:
                success_count += 1
                self._kiosk_obj.record_purchase(user_id)
                self._kiosk_obj.check_and_activate_emergency()
            else:
                print(f"  STOPPED at unit {i+1} — purchase failed.")
                break

        if success_count > 0:
            self._persist()

            remaining = product.get_available_stock()
            if remaining <= 5:
                print(f"\n  *** WARNING: Only {remaining} unit(s) left for '{item_name}' ***")

        if success_count > 0 and success_count < quantity:
            print(f"  Partial success: {success_count}/{quantity} purchased.")

        return success_count > 0

    def refund_transaction(self, txn_id: str, user_id: str) -> bool:

        print(f"\n[KioskInterface] Refund txn: {txn_id} | User: {user_id}")

        transactions = FileHandler.load_transactions()
        txn = next(
            (t for t in transactions
             if t.get("txn_id") == txn_id and t.get("user_id") == user_id),
            None
        )

        product = None
        if txn:
            product = self._kiosk_obj._inventory.find_item(txn.get("item", ""))

        command = RefundCommand(
            kiosk_id=self._kiosk_obj.kiosk_id,
            user_id=user_id,
            txn_id=txn_id,
            item=product,
            payment_processor=self._kiosk_obj._payment_processor,
        )

        result = command.execute()
        self._history_log.record(command)

        if result:
            self._persist()

        return result

    def restock_inventory(self, item_name: str, quantity: int,
                          admin_id: str = "admin") -> bool:

        print(f"\n[KioskInterface] Restock: {quantity}x '{item_name}'")

        product = self._kiosk_obj._inventory.find_item(item_name)
        if not product:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        command = RestockCommand(
            kiosk_id=self._kiosk_obj.kiosk_id,
            user_id=admin_id,
            item=product,
            quantity=quantity,
        )

        result = command.execute()
        self._history_log.record(command)

        if result:
            if (self._kiosk_obj._emergency_mode and
                    not self._kiosk_obj._inventory.get_low_stock_items(5)):
                self._kiosk_obj.deactivate_emergency_mode()

            self._persist()

        return result

    def run_diagnostics(self) -> dict:

        print(f"\n[KioskInterface] Diagnostics: {self._kiosk_obj.kiosk_id}")

        hw = self._kiosk_obj._hardware
        if not hw:
            print("  No hardware attached.")
            return {}

        print(f"  Status      : {hw.get_status()}")
        print(f"  Capabilities: {hw.get_capabilities()}")
        print(f"  Healthy     : {hw.is_healthy()}")

        report = hw.run_diagnostics()

        if self._kiosk_obj._sensors:
            report["sensors"] = self._kiosk_obj._sensors.run_diagnostics()
            self._kiosk_obj._sensors.display()

        for k, v in report.items():
            if k != "kiosk_id":
                print(f"  {k}: {v}")

        return report

    def show_inventory(self):
        print(f"\n[KioskInterface] Inventory — {self._kiosk_obj.kiosk_id}:")
        self._kiosk_obj._inventory.display()

    def show_kiosk_info(self):
        self._kiosk_obj.display_info()

    def get_user_transactions(self, user_id: str) -> list:
        return [
            txn for txn in FileHandler.load_transactions()
            if txn.get("user_id") == user_id
        ]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _persist(self):
        """Persist kiosk state."""
        FileHandler.save_kiosk(
            self._kiosk_obj.kiosk_id,
            self._kiosk_obj.to_dict()
        )