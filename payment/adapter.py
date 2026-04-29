"""
DESIGN PATTERN: Adapter
File: payment/adapter.py
Purpose: Wraps incompatible UPI, Card, and Wallet third-party APIs
         into the common PaymentProcessor interface.

Pattern participants:
  Target    → PaymentProcessor         (payment/payment_interface.py)
  Adaptee 1 → UPISystemAPI             (incompatible raw UPI API)
  Adaptee 2 → CardGatewayAPI           (incompatible raw Card API)
  Adaptee 3 → DigitalWalletAPI         (incompatible raw Wallet API)
  Adapter 1 → UPIAdapter               (wraps UPISystemAPI)
  Adapter 2 → CardAdapter              (wraps CardGatewayAPI)
  Adapter 3 → DigitalWalletAdapter     (wraps DigitalWalletAPI)
  Client    → KioskInterface / commands (uses only PaymentProcessor)
"""

from payment.payment_interface import PaymentProcessor


# ── Adaptees (incompatible third-party APIs) ──────────────────────────────────

class UPISystemAPI:
    """Raw UPI API — incompatible with PaymentProcessor interface."""

    def initiate_upi_payment(self, vpa: str, rupees: float) -> bool:
        print(f"  [UPI API] Paying Rs.{rupees:.2f} to {vpa}")
        return True

    def upi_refund(self, vpa: str, rupees: float) -> bool:
        print(f"  [UPI API] Refunding Rs.{rupees:.2f} to {vpa}")
        return True

    def check_upi_status(self, vpa: str) -> str:
        return "ACTIVE"


class CardGatewayAPI:
    """Raw Card API — incompatible with PaymentProcessor interface."""

    def charge_card(self, token: str, paise: int) -> dict:
        print(f"  [Card API] Charging {paise} paise via {token}")
        return {"status": "SUCCESS", "txn_id": f"CC-{token[:4]}"}

    def reverse_charge(self, txn_id: str) -> bool:
        print(f"  [Card API] Reversing {txn_id}")
        return True

    def get_card_info(self, token: str) -> dict:
        return {"token": token, "type": "VISA", "status": "VALID"}


class DigitalWalletAPI:
    """Raw Wallet API — incompatible with PaymentProcessor interface."""

    def debit_wallet(self, wallet_id: str, value: float) -> str:
        print(f"  [Wallet API] Debiting Rs.{value:.2f} from {wallet_id}")
        return f"WLT-{int(value*10)}"

    def credit_wallet(self, wallet_id: str, value: float, ref: str) -> bool:
        print(f"  [Wallet API] Crediting Rs.{value:.2f} back to {wallet_id}")
        return True


# ── Adapters ──────────────────────────────────────────────────────────────────

class UPIAdapter(PaymentProcessor):
    """ADAPTER: Translates UPISystemAPI → PaymentProcessor."""

    def __init__(self, vpa: str):
        self._api = UPISystemAPI()
        self._vpa = vpa

    def process_payment(self, amount: float, user_id: str) -> bool:
        return self._api.initiate_upi_payment(self._vpa, amount)

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        return self._api.upi_refund(self._vpa, amount)

    def get_provider_name(self) -> str:
        return f"UPI ({self._vpa})"

    def to_dict(self) -> dict:
        return {"type": "upi", "vpa": self._vpa}


class CardAdapter(PaymentProcessor):
    """ADAPTER: Translates CardGatewayAPI → PaymentProcessor."""

    def __init__(self, card_token: str):
        self._api   = CardGatewayAPI()
        self._token = card_token

    def process_payment(self, amount: float, user_id: str) -> bool:
        result = self._api.charge_card(self._token, int(amount * 100))
        return result.get("status") == "SUCCESS"

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        return self._api.reverse_charge(transaction_id)

    def get_provider_name(self) -> str:
        return f"Card ({self._token})"

    def to_dict(self) -> dict:
        return {"type": "card", "token": self._token}


class DigitalWalletAdapter(PaymentProcessor):
    """ADAPTER: Translates DigitalWalletAPI → PaymentProcessor."""

    def __init__(self, wallet_id: str):
        self._api       = DigitalWalletAPI()
        self._wallet_id = wallet_id

    def process_payment(self, amount: float, user_id: str) -> bool:
        return self._api.debit_wallet(self._wallet_id, amount) is not None

    def refund_payment(self, transaction_id: str, amount: float) -> bool:
        return self._api.credit_wallet(self._wallet_id, amount, transaction_id)

    def get_provider_name(self) -> str:
        return f"Wallet ({self._wallet_id})"

    def to_dict(self) -> dict:
        return {"type": "wallet", "wallet_id": self._wallet_id}


# ── Restore from saved dict ───────────────────────────────────────────────────

def payment_from_dict(d: dict) -> PaymentProcessor:
    """Rebuild a PaymentProcessor from a saved dict."""
    t = d.get("type")
    if t == "upi":
        return UPIAdapter(d["vpa"])
    elif t == "card":
        return CardAdapter(d["token"])
    elif t == "wallet":
        return DigitalWalletAdapter(d["wallet_id"])
    return UPIAdapter("default@upi")
