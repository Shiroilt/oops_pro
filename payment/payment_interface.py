"""
File: payment/payment_interface.py
Purpose: Abstract base class that all payment processors must implement.
         This is the TARGET interface used by the Adapter pattern.
"""

from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    """
    Abstract interface for all payment methods.
    Any new payment provider must implement these three methods.
    The kiosk depends ONLY on this interface — never on a specific provider.
    """

    @abstractmethod
    def process_payment(self, amount: float, user_id: str) -> bool:
        """
        Attempt to charge the user for the given amount.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        """
        Refund a previous transaction.
        Returns True if refund was successful.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return a human-readable name for this payment provider."""
        pass
