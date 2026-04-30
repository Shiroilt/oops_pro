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
        """
        Executes the complex transactional flow for a purchase operation.
        Guarantees atomicity via the Command pattern structure.
        """
        import uuid
        generated_uuid = str(uuid.uuid4())
        self.txn_id = generated_uuid[:8].upper()

        # Phase 1: Validate Hardware constraints
        is_refrigerated_item = getattr(self._item, 'requires_refrigeration', False)
        if is_refrigerated_item:
            active_hardware = self._kiosk_ref._hardware
            has_fridge = "refrigeration" in active_hardware.get_capabilities() if active_hardware else False
            
            if not has_fridge:
                self.status = "FAILED"
                self.log_message = f"'{self.item_name}' needs refrigeration — module not installed"
                EventBus().publish(TransactionFailedEvent(self.kiosk_id, self.log_message))
                print(f"  ERROR: {self.log_message}")
                return False

        # Phase 2: Inventory Availability Check
        is_item_in_stock = self._item.is_available()
        if not is_item_in_stock:
            self.status = "FAILED"
            self.log_message = f"'{self.item_name}' is out of stock"
            print(f"  ERROR: {self.log_message}")
            return False

        # Phase 3: Initiate Atomic Reservation
        self._item.reserve()
        self._reserved = True

        # Phase 4: Compute Dynamic Contextual Price
        raw_price = self._item.get_price()
        self.final_price = self._pricing.get_price(raw_price)

        # Phase 5: Execute External Payment processing
        is_payment_successful = self._payment.process_payment(self.final_price, self.user_id)
        if not is_payment_successful:
            self.status = "FAILED"
            self.log_message = "Payment failed"
            self.undo() # Trigger atomic rollback
            EventBus().publish(TransactionFailedEvent(self.kiosk_id, self.log_message))
            print(f"  ERROR: {self.log_message} — rolling back")
            return False
            
        self._paid = True

        # Phase 6: Finalize Stock Deduction
        self._item.confirm_sale()
        self._reserved = False

        # Phase 7: Evaluate Low Stock Thresholds
        current_inventory_level = self._item.get_available_stock()
        is_low_stock = current_inventory_level <= LOW_STOCK_THRESHOLD
        if is_low_stock:
            EventBus().publish(LowStockEvent(self.kiosk_id, self.item_name, current_inventory_level))

        # Phase 8: Data Persistence and Audit Logging
        self.status = "SUCCESS"
        payment_method_name = self._payment.get_provider_name()
        
        self.log_message = (f"Purchased '{self.item_name}' for "
                            f"Rs.{self.final_price:.2f} via "
                            f"{payment_method_name}")

        transaction_record = {
            "txn_id":    self.txn_id,
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "item":      self.item_name,
            "amount":    self.final_price,
            "provider":  payment_method_name,
            "timestamp": self.timestamp,
            "status":    "SUCCESS",
            "type":      "PURCHASE",
        }
        FileHandler.save_transaction(transaction_record)

        print(f"  SUCCESS: {self.log_message}")
        return True

    def undo(self):
        """Rollback — release reservation if payment was not taken."""
        if self._reserved and not self._paid:
            self._item.release_reservation()
            self._reserved = False
        self.status = "UNDONE"
        print(f"  [Rollback] Purchase of '{self.item_name}' reversed.")
