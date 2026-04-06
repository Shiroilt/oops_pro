"""
File: payment/card_payment.py
Purpose: Simulates an existing third-party credit/debit card gateway.
         This class has its OWN incompatible API — it is the ADAPTEE.
         The kiosk cannot use this directly; it needs an Adapter.
"""


class CardGatewayAPI:
    """
    Third-party card payment gateway with its own incompatible API.
    ADAPTEE in the Adapter pattern.
    """

    def charge_card(self, card_token: str, amount_paise: int) -> dict:
        """
        Card-specific method — charges in paise (1 Rs = 100 paise).
        Not compatible with PaymentProcessor interface.
        """
        print(f"  [Card API] Charging {amount_paise} paise via token: {card_token}")
        return {
            "status": "SUCCESS",
            "txn_id": f"CC-{card_token[:4]}-{amount_paise}",
            "gateway": "CardGateway v2"
        }

    def reverse_charge(self, txn_id: str) -> bool:
        """Card-specific reversal method."""
        print(f"  [Card API] Reversing transaction: {txn_id}")
        return True

    def get_card_info(self, card_token: str) -> dict:
        """Card-specific info method."""
        return {"token": card_token, "type": "VISA", "status": "VALID"}
