"""
DESIGN PATTERN: Command (Behavioral)
File: commands/refund_command.py
Purpose: Refund a previous purchase atomically.
         Validates the transaction belongs to the requesting user.
         Restores stock and marks original transaction as REFUNDED.
"""

from commands.command import Command
from persistence.file_handler import FileHandler


class RefundCommand(Command):
    """
    COMMAND: Processes a refund.
    Validates ownership of the transaction before proceeding.
    Restores inventory stock on success.
    """

    def __init__(self, kiosk_id: str, user_id: str, txn_id: str,
                 item, payment_processor):
        super().__init__(kiosk_id, user_id)
        self.txn_id        = txn_id
        self._item         = item
        self._payment      = payment_processor
        self._refund_done  = False
        self.item_name     = item.get_name() if item else "Unknown"
        self.refund_amount = 0.0

    def execute(self) -> bool:
        # Step 1: Verify transaction belongs to this user and is refundable
        all_txns = FileHandler.load_transactions()
        txn = next((t for t in all_txns
                    if t.get("txn_id") == self.txn_id
                    and t.get("user_id") == self.user_id
                    and t.get("status") == "SUCCESS"), None)

        if not txn:
            self.status      = "FAILED"
            self.log_message = (f"Transaction '{self.txn_id}' not found "
                                f"or does not belong to user '{self.user_id}'")
            print(f"  ERROR: {self.log_message}")
            return False

        self.refund_amount = txn.get("amount", 0.0)
        self.item_name     = txn.get("item", self.item_name)

        # Step 2: Process refund via payment provider
        refund_ok = self._payment.refund_payment(self.txn_id, self.refund_amount)
        if not refund_ok:
            self.status      = "FAILED"
            self.log_message = "Payment provider rejected refund"
            print(f"  ERROR: {self.log_message}")
            return False

        # Step 3: Restore stock
        if self._item and hasattr(self._item, '_stock'):
            self._item._stock += 1
        self._refund_done = True

        # Step 4: Mark original transaction as REFUNDED in file
        data = FileHandler.load()
        for t in data["transactions"]:
            if t.get("txn_id") == self.txn_id:
                t["status"] = "REFUNDED"
        FileHandler.save(data)

        # Step 5: Log the refund transaction
        self.status      = "SUCCESS"
        self.log_message = (f"Refunded '{self.item_name}' "
                            f"Rs.{self.refund_amount:.2f} to '{self.user_id}'")

        FileHandler.save_transaction({
            "txn_id":    f"REF-{self.txn_id}",
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "item":      self.item_name,
            "amount":    self.refund_amount,
            "provider":  self._payment.get_provider_name() if self._payment else "N/A",
            "timestamp": self.timestamp,
            "status":    "SUCCESS",
            "type":      "REFUND",
        })

        print(f"  SUCCESS: {self.log_message}")
        return True

    def undo(self):
        """Reverse a refund — re-deduct stock."""
        if self._refund_done and self._item and hasattr(self._item, '_stock'):
            self._item._stock = max(0, self._item._stock - 1)
        self.status = "UNDONE"
        print(f"  [Rollback] Refund of '{self.item_name}' reversed.")
