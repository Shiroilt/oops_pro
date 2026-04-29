"""
DESIGN PATTERN: Command (Behavioral)
File: commands/purchase_command.py
Purpose: Atomic purchase operation.
         Steps: reserve stock → process payment → confirm sale.
         If any step fails → full rollback automatically.
         Fires city-monitor events on low stock or failure.
"""

from commands.command import Command
from city_monitor.monitor import EventBus, TransactionFailedEvent, LowStockEvent
from persistence.file_handler import FileHandler

LOW_STOCK_THRESHOLD = 5


class PurchaseCommand(Command):
    """
    COMMAND: Executes a purchase atomically.
    Rollback releases the stock reservation if payment fails.
    """

    def __init__(self, kiosk_id: str, user_id: str, item,
                 payment_processor, pricing_context, kiosk_ref):
        super().__init__(kiosk_id, user_id)
        self._item      = item
        self._payment   = payment_processor
        self._pricing   = pricing_context
        self._kiosk_ref = kiosk_ref
        self._paid      = False
        self._reserved  = False
        self.item_name  = item.get_name()
        self.final_price = 0.0
        self.txn_id     = None

    def execute(self) -> bool:
        import uuid
        self.txn_id = str(uuid.uuid4())[:8].upper()

        # Step 1: Check hardware dependency for chilled items
        if (hasattr(self._item, 'requires_refrigeration')
                and self._item.requires_refrigeration):
            hw = self._kiosk_ref._hardware
            if hw and "refrigeration" not in hw.get_capabilities():
                self.status      = "FAILED"
                self.log_message = (f"'{self.item_name}' needs refrigeration "
                                    f"— module not installed")
                EventBus().publish(
                    TransactionFailedEvent(self.kiosk_id, self.log_message))
                print(f"  ERROR: {self.log_message}")
                return False

        # Step 2: Check stock
        if not self._item.is_available():
            self.status      = "FAILED"
            self.log_message = f"'{self.item_name}' is out of stock"
            print(f"  ERROR: {self.log_message}")
            return False

        # Step 3: Reserve stock (atomic start)
        self._item.reserve()
        self._reserved = True

        # Step 4: Compute dynamic price via Strategy
        self.final_price = self._pricing.get_price(self._item.get_price())

        # Step 5: Process payment
        payment_ok = self._payment.process_payment(self.final_price, self.user_id)
        if not payment_ok:
            self.status      = "FAILED"
            self.log_message = "Payment failed"
            self.undo()
            EventBus().publish(
                TransactionFailedEvent(self.kiosk_id, self.log_message))
            print(f"  ERROR: {self.log_message} — rolling back")
            return False
        self._paid = True

        # Step 6: Confirm sale (reduce actual stock)
        self._item.confirm_sale()
        self._reserved = False

        # Step 7: Check low stock and fire event
        remaining = self._item.get_available_stock()
        if remaining <= LOW_STOCK_THRESHOLD:
            EventBus().publish(
                LowStockEvent(self.kiosk_id, self.item_name, remaining))

        # Step 8: Log and persist
        self.status      = "SUCCESS"
        self.log_message = (f"Purchased '{self.item_name}' for "
                            f"Rs.{self.final_price:.2f} via "
                            f"{self._payment.get_provider_name()}")

        FileHandler.save_transaction({
            "txn_id":    self.txn_id,
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "item":      self.item_name,
            "amount":    self.final_price,
            "provider":  self._payment.get_provider_name(),
            "timestamp": self.timestamp,
            "status":    "SUCCESS",
            "type":      "PURCHASE",
        })

        print(f"  SUCCESS: {self.log_message}")
        return True

    def undo(self):
        """Rollback — release reservation if payment was not taken."""
        if self._reserved and not self._paid:
            self._item.release_reservation()
            self._reserved = False
        self.status = "UNDONE"
        print(f"  [Rollback] Purchase of '{self.item_name}' reversed.")
