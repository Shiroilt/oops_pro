"""
DESIGN PATTERN: Strategy (Behavioral)
File: payment/payment_selector.py
Purpose: User selects payment method AT PURCHASE TIME.
         Each payment adapter IS a strategy implementing PaymentProcessor.
         PaymentSelector presents options and returns the chosen strategy.

This is the NEW feature — previously payment was chosen at kiosk creation.
Now users pick UPI / Card / Wallet each time they buy something.
"""

from payment.adapter import UPIAdapter, CardAdapter, DigitalWalletAdapter
from payment.payment_interface import PaymentProcessor


class PaymentSelector:
    """
    STRATEGY SELECTOR: Presents payment options and returns the
    chosen PaymentProcessor (Strategy) for this transaction.

    Called at purchase time — never at kiosk setup time.
    """

    @staticmethod
    def select_payment() -> PaymentProcessor:
        """
        Interactively ask the user to choose a payment method.
        Returns the configured PaymentProcessor, or None if cancelled.
        """
        print("\n  ─── SELECT PAYMENT METHOD ───────────────────────")
        print("    1. UPI     — enter your VPA (e.g. name@bank)")
        print("    2. Card    — enter your card token")
        print("    3. Wallet  — enter your wallet ID")
        print("    0. Cancel")
        print("  ─────────────────────────────────────────────────")

        while True:
            choice = input("  Your choice (0-3): ").strip()

            if choice == "0":
                return None

            elif choice == "1":
                vpa = input("  UPI VPA (e.g. user@paytm): ").strip()
                if not vpa:
                    vpa = "user@upi"
                processor = UPIAdapter(vpa=vpa)
                print(f"  Payment method: UPI → {vpa}")
                return processor

            elif choice == "2":
                token = input("  Card token (e.g. VISA-1234): ").strip()
                if not token:
                    token = "CARD-0001"
                processor = CardAdapter(card_token=token)
                print(f"  Payment method: Card → {token}")
                return processor

            elif choice == "3":
                wid = input("  Wallet ID (e.g. WALLET-001): ").strip()
                if not wid:
                    wid = "WALLET-001"
                processor = DigitalWalletAdapter(wallet_id=wid)
                print(f"  Payment method: Wallet → {wid}")
                return processor

            else:
                print("  Invalid choice. Enter 0, 1, 2, or 3.")
