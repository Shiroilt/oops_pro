"""
DESIGN PATTERN: Adapter
File: payment/adapter.py
Purpose: Wraps incompatible third-party payment APIs (UPI, Card, Wallet)
         into the common PaymentProcessor interface.
         The kiosk only depends on PaymentProcessor — never on specific APIs.
"""

from payment.payment_interface import PaymentProcessor
from payment.upi_payment import UPISystemAPI
from payment.card_payment import CardGatewayAPI


# ── Adapter 1: UPI ────────────────────────────────────────────────────────────

class UPIAdapter(PaymentProcessor):
    """
    ADAPTER: Translates UPISystemAPI into the PaymentProcessor interface.
    """

    def __init__(self, vpa: str):
        self._upi_api = UPISystemAPI()      # incompatible adaptee
        self._vpa = vpa

    def process_payment(self, amount: float, user_id: str) -> bool:
        # Translate: PaymentProcessor.process_payment → UPI.initiate_upi_payment
        return self._upi_api.initiate_upi_payment(self._vpa, amount)

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        # Translate: PaymentProcessor.refund_payment → UPI.upi_refund
        return self._upi_api.upi_refund(self._vpa, amount)

    def get_provider_name(self) -> str:
        return "UPI System"


# ── Adapter 2: Credit/Debit Card ──────────────────────────────────────────────

class CardAdapter(PaymentProcessor):
    """
    ADAPTER: Translates CardGatewayAPI into the PaymentProcessor interface.
    """

    def __init__(self, card_token: str):
        self._card_api = CardGatewayAPI()   # incompatible adaptee
        self._card_token = card_token
        self._last_txn_id = None

    def process_payment(self, amount: float, user_id: str) -> bool:
        # Translate: amount (Rs float) → paise (int) for the card API
        amount_paise = int(amount * 100)
        result = self._card_api.charge_card(self._card_token, amount_paise)
        self._last_txn_id = result.get("txn_id")
        return result.get("status") == "SUCCESS"

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        # Translate: PaymentProcessor.refund_payment → CardGateway.reverse_charge
        return self._card_api.reverse_charge(transaction_id)

    def get_provider_name(self) -> str:
        return "Card Gateway"


# ── Adapter 3: Digital Wallet ─────────────────────────────────────────────────

class DigitalWalletAPI:
    """Simulated digital wallet with yet another incompatible API."""

    def debit_wallet(self, wallet_id: str, value: float) -> str:
        print(f"  [Wallet API] Debiting Rs.{value:.2f} from wallet {wallet_id}")
        return f"WLT-TXN-{int(value * 10)}"

    def credit_wallet(self, wallet_id: str, value: float, ref: str) -> bool:
        print(f"  [Wallet API] Crediting Rs.{value:.2f} back to wallet {wallet_id}")
        return True


class DigitalWalletAdapter(PaymentProcessor):
    """
    ADAPTER: Translates DigitalWalletAPI into the PaymentProcessor interface.
    """

    def __init__(self, wallet_id: str):
        self._wallet_api = DigitalWalletAPI()   # incompatible adaptee
        self._wallet_id = wallet_id

    def process_payment(self, amount: float, user_id: str) -> bool:
        txn = self._wallet_api.debit_wallet(self._wallet_id, amount)
        return txn is not None

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        return self._wallet_api.credit_wallet(self._wallet_id, amount, transaction_id)

    def get_provider_name(self) -> str:
        return "Digital Wallet"
