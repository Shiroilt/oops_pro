"""
DESIGN PATTERN: Facade
File: core/kiosk_interface.py
Purpose: Provides a simplified interface for interacting with kiosk operations.

         External clients interact ONLY with this class.
         Internally, operations are executed via Command pattern.

         This layer hides:
         - Inventory management
         - Payment processing
         - Hardware interaction
         - Persistence logic
"""

from core.kiosk import Kiosk
from commands.command import CommandHistory
from commands.purchase_command import PurchaseCommand
from commands.refund_command import RefundCommand
from commands.restock_command import RestockCommand
from persistence.file_handler import FileHandler


class KioskInterface:
    """
    FACADE CLASS:
    Central interface for all kiosk operations.

    Responsibilities:
    - Delegate actions using command objects
    - Maintain execution history
    - Ensure safe and consistent interactions
    """

    def __init__(self, kiosk: Kiosk):
        self._kiosk_ref   = kiosk
        self._cmd_history = CommandHistory()

    # ── Public API ────────────────────────────────────────────────────────────

    def purchase_item(self, item_name: str, user_id: str,
                      quantity: int = 1) -> bool:

        print(f"\n[KioskInterface] Purchase: {quantity}x '{item_name}' | User: {user_id}")

        if not self._kiosk_ref.is_operational():
            print(f"  ERROR: Kiosk is {self._kiosk_ref.get_mode()} — cannot purchase.")
            return False

        if self._kiosk_ref._payment_processor is None:
            print("  ERROR: No payment method configured.")
            return False

        item_obj = self._kiosk_ref._inventory.find_item(item_name)
        if not item_obj:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        if item_obj.get_available_stock() < quantity:
            print(f"  ERROR: Only {item_obj.get_available_stock()} unit(s) available "
                  f"but {quantity} requested.")
            return False

        success_counter = 0

        for i in range(quantity):

            if not self._kiosk_ref.can_user_purchase(user_id):
                print(f"  STOPPED: Limit reached after {success_counter} item(s).")
                break

            cmd = PurchaseCommand(
                kiosk_id=self._kiosk_ref.kiosk_id,
                user_id=user_id,
                item=item_obj,
                payment_processor=self._kiosk_ref._payment_processor,
                pricing_context=self._kiosk_ref._pricing,
                kiosk_ref=self._kiosk_ref,
            )

            result = cmd.execute()
            self._cmd_history.record(cmd)

            if result:
                success_counter += 1
                self._kiosk_ref.record_purchase(user_id)
                self._kiosk_ref.check_and_activate_emergency()
            else:
                print(f"  STOPPED at unit {i+1} — purchase failed.")
                break

        if success_counter > 0:
            self._persist_state()

            remaining_stock = item_obj.get_available_stock()
            if remaining_stock <= 5:
                print(f"\n  *** WARNING: Only {remaining_stock} unit(s) of "
                      f"'{item_name}' left! ***")

        if success_counter > 0 and success_counter < quantity:
            print(f"  Partial success: {success_counter}/{quantity} purchased.")

        return success_counter > 0

    def refund_transaction(self, txn_id: str, user_id: str) -> bool:

        print(f"\n[KioskInterface] Refund txn: {txn_id} | User: {user_id}")

        all_txns = FileHandler.load_transactions()
        txn_data = next(
            (t for t in all_txns
             if t.get("txn_id") == txn_id and t.get("user_id") == user_id),
            None
        )

        item_obj = None
        if txn_data:
            item_obj = self._kiosk_ref._inventory.find_item(txn_data.get("item", ""))

        cmd = RefundCommand(
            kiosk_id=self._kiosk_ref.kiosk_id,
            user_id=user_id,
            txn_id=txn_id,
            item=item_obj,
            payment_processor=self._kiosk_ref._payment_processor,
        )

        success = cmd.execute()
        self._cmd_history.record(cmd)

        if success:
            self._persist_state()

        return success

    def restock_inventory(self, item_name: str, quantity: int,
                          admin_id: str = "admin") -> bool:

        print(f"\n[KioskInterface] Restock: {quantity}x '{item_name}'")

        item_obj = self._kiosk_ref._inventory.find_item(item_name)
        if not item_obj:
            print(f"  ERROR: '{item_name}' not found.")
            return False

        cmd = RestockCommand(
            kiosk_id=self._kiosk_ref.kiosk_id,
            user_id=admin_id,
            item=item_obj,
            quantity=quantity,
        )

        success = cmd.execute()
        self._cmd_history.record(cmd)

        if success:
            if (self._kiosk_ref._emergency_mode and
                    not self._kiosk_ref._inventory.get_low_stock_items(5)):
                self._kiosk_ref.deactivate_emergency_mode()

            self._persist_state()

        return success

    def run_diagnostics(self) -> dict:

        print(f"\n[KioskInterface] Diagnostics: {self._kiosk_ref.kiosk_id}")

        hardware = self._kiosk_ref._hardware
        if not hardware:
            print("  No hardware attached.")
            return {}

        print(f"  Status      : {hardware.get_status()}")
        print(f"  Capabilities: {hardware.get_capabilities()}")
        print(f"  Healthy     : {hardware.is_healthy()}")

        diag_report = hardware.run_diagnostics()

        if self._kiosk_ref._sensors:
            diag_report["sensors"] = self._kiosk_ref._sensors.run_diagnostics()
            self._kiosk_ref._sensors.display()

        for key, value in diag_report.items():
            if key != "kiosk_id":
                print(f"  {key}: {value}")

        return diag_report

    def show_inventory(self):
        print(f"\n[KioskInterface] Inventory — {self._kiosk_ref.kiosk_id}:")
        self._kiosk_ref._inventory.display()

    def show_kiosk_info(self):
        self._kiosk_ref.display_info()

    def get_user_transactions(self, user_id: str) -> list:
        return [
            txn for txn in FileHandler.load_transactions()
            if txn.get("user_id") == user_id
        ]

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _persist_state(self):
        """Save kiosk state after any successful operation."""
        FileHandler.save_kiosk(
            self._kiosk_ref.kiosk_id,
            self._kiosk_ref.to_dict()
        )