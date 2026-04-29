"""
DESIGN PATTERN: Command (Behavioral)
File: commands/command.py
Purpose: Base Command class. Every operation (purchase, refund, restock)
         is a Command object. Supports atomic execution and undo/rollback.
         CommandHistory keeps a full audit log of all executed commands.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class Command(ABC):
    """
    Abstract Command — all operations implement execute() and undo().
    Atomic: if execute() fails partway, undo() restores previous state.
    """

    def __init__(self, kiosk_id: str, user_id: str):
        self.kiosk_id    = kiosk_id
        self.user_id     = user_id
        self.timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status      = "PENDING"    # PENDING | SUCCESS | FAILED | UNDONE
        self.log_message = ""

    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True on success, False on failure."""
        pass

    @abstractmethod
    def undo(self):
        """Rollback — restore previous state if execution failed."""
        pass

    def get_log(self) -> dict:
        return {
            "type":      self.__class__.__name__,
            "kiosk_id":  self.kiosk_id,
            "user_id":   self.user_id,
            "timestamp": self.timestamp,
            "status":    self.status,
            "message":   self.log_message,
        }

    def __str__(self):
        return (f"[{self.timestamp}] {self.__class__.__name__} | "
                f"Kiosk: {self.kiosk_id} | User: {self.user_id} | "
                f"Status: {self.status} | {self.log_message}")


class CommandHistory:
    """
    Singleton audit log of all executed Commands.
    Used for transaction history and system-wide audit trail.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history = []
        return cls._instance

    def record(self, command: Command):
        self._history.append(command)

    def get_all(self) -> list:
        return list(self._history)

    def get_by_user(self, user_id: str) -> list:
        return [c for c in self._history if c.user_id == user_id]

    def get_by_kiosk(self, kiosk_id: str) -> list:
        return [c for c in self._history if c.kiosk_id == kiosk_id]

    def get_successful_purchases_by_user(self, user_id: str) -> list:
        from commands.purchase_command import PurchaseCommand
        return [c for c in self._history
                if isinstance(c, PurchaseCommand)
                and c.user_id == user_id
                and c.status == "SUCCESS"]

    def display(self, kiosk_id: str = None):
        history = self.get_by_kiosk(kiosk_id) if kiosk_id else self._history
        if not history:
            print("  No command history found.")
            return
        for cmd in history:
            print(f"  {cmd}")
