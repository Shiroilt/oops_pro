"""
File: payment/payment_interface.py
Purpose: Abstract PaymentProcessor interface — TARGET for Adapter pattern.
         All payment providers must implement this contract.
         The kiosk depends ONLY on this interface, never on specific APIs.
"""

from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    """Target interface — kiosk depends ONLY on this, never on specific APIs."""

    @abstractmethod
    def process_payment(self, amount: float, user_id: str) -> bool:
        """Process a payment of `amount` for `user_id`. Returns True on success."""
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        """Refund a previously processed payment. Returns True on success."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return a human-readable name for this payment provider."""
        pass
