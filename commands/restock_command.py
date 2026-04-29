"""
DESIGN PATTERN: Command (Behavioral)
File: commands/restock_command.py
Purpose: Admin-only restock operation.
         Fires RestockEvent so city monitor is notified.
         Supports undo (removes added stock).
"""

from commands.command import Command
from city_monitor.monitor import EventBus, RestockEvent
from persistence.file_handler import FileHandler


class RestockCommand(Command):
    """
    COMMAND: Adds stock to an inventory item.
    Admin-guarded — should only be called via admin flow.
    Fires RestockEvent and persists updated inventory.
    """

    def __init__(self, kiosk_id: str, user_id: str, item, quantity: int):
        super().__init__(kiosk_id, user_id)
        self._item           = item
        self._quantity       = quantity
        self._previous_stock = 0
        self.item_name       = item.get_name()

    def execute(self) -> bool:
        if self._quantity <= 0:
            self.status      = "FAILED"
            self.log_message = "Quantity must be greater than zero"
            print(f"  ERROR: {self.log_message}")
            return False

        # Save current stock for undo
        self._previous_stock = self._item.get_available_stock()

        # Add stock
        self._item.restock(self._quantity)

        # Notify city monitor
        EventBus().publish(
            RestockEvent(self.kiosk_id, self.item_name, self._quantity))

        # Log and persist
        self.status      = "SUCCESS"
        self.log_message = (f"Restocked '{self.item_name}' "
                            f"+{self._quantity} units. "
                            f"New stock: {self._item.get_available_stock()}")

        FileHandler.save_transaction({
            "txn_id":    f"RST-{self.kiosk_id}-{self.timestamp.replace(' ','-')}",
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "item":      self.item_name,
            "quantity":  self._quantity,
            "timestamp": self.timestamp,
            "status":    "SUCCESS",
            "type":      "RESTOCK",
        })

        print(f"  SUCCESS: {self.log_message}")
        return True

    def undo(self):
        """Remove the added stock."""
        self._item._stock = self._previous_stock
        self.status       = "UNDONE"
        print(f"  [Rollback] Restock of '{self.item_name}' reversed.")
