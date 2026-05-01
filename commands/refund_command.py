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
        """
        Executes the transactional flow for a refund operation.
        Verifies ownership, interacts with the payment provider,
        and restores the inventory stock on success.
        """
        # Phase 1: Retrieve and validate historical transaction records
        historical_transactions = FileHandler.load_transactions()
        
        target_transaction = None
        for record in historical_transactions:
            is_matching_txn = (record.get("txn_id") == self.txn_id)
            is_matching_user = (record.get("user_id") == self.user_id)
            is_successful_txn = (record.get("status") == "SUCCESS")
            
            if is_matching_txn and is_matching_user and is_successful_txn:
                target_transaction = record
                break

        if target_transaction is None:
            self.status = "FAILED"
            self.log_message = f"Transaction '{self.txn_id}' not found or does not belong to user '{self.user_id}'"
            print(f"  ERROR: {self.log_message}")
            return False

        # Phase 2: Extract transaction payload details
        self.refund_amount = target_transaction.get("amount", 0.0)
        self.item_name = target_transaction.get("item", self.item_name)

        # Phase 3: Initiate external payment refund sequence
        is_provider_refund_successful = self._payment.refund_payment(self.txn_id, self.refund_amount)
        if not is_provider_refund_successful:
            self.status = "FAILED"
            self.log_message = "Payment provider rejected refund"
            print(f"  ERROR: {self.log_message}")
            return False

        # Phase 4: Reintegrate stock into available inventory
        has_item_reference = self._item is not None
        has_stock_attribute = hasattr(self._item, '_stock')
        
        if has_item_reference and has_stock_attribute:
            self._item._stock += 1
            
        self._refund_done = True

        # Phase 5: Mutate global state to reflect refunded status
        global_data_blob = FileHandler.load()
        for transaction_entry in global_data_blob["transactions"]:
            if transaction_entry.get("txn_id") == self.txn_id:
                transaction_entry["status"] = "REFUNDED"
                
        FileHandler.save(global_data_blob)

        # Phase 6: Construct and persist the audit trail record
        self.status = "SUCCESS"
        self.log_message = f"Refunded '{self.item_name}' Rs.{self.refund_amount:.2f} to '{self.user_id}'"
        
        provider_name = self._payment.get_provider_name() if self._payment else "N/A"

        audit_record = {
            "txn_id":    f"REF-{self.txn_id}",
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "item":      self.item_name,
            "amount":    self.refund_amount,
            "provider":  provider_name,
            "timestamp": self.timestamp,
            "status":    "SUCCESS",
            "type":      "REFUND",
        }
        
        FileHandler.save_transaction(audit_record)

        print(f"  SUCCESS: {self.log_message}")
        return True

    def undo(self):
        """Reverse a refund — re-deduct stock."""
        if self._refund_done and self._item and hasattr(self._item, '_stock'):
            self._item._stock = max(0, self._item._stock - 1)
        self.status = "UNDONE"
        print(f"  [Rollback] Refund of '{self.item_name}' reversed.")
