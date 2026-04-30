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
        Presents the interactive payment prompt and returns the configured adapter instance.
        """
        # Display the main payment selection header
        print("\n  ─── SELECT PAYMENT METHOD ───────────────────────")
        print("    1. UPI     — enter your VPA (e.g. name@bank)")
        print("    2. Card    — enter your card token")
        print("    3. Wallet  — enter your wallet ID")
        print("    0. Cancel")
        print("  ─────────────────────────────────────────────────")

        # Loop until a valid choice is made
        while True:
            user_input = input("  Your choice (0-3): ").strip()

            if user_input == "0":
                # User cancelled the payment flow
                return None

            elif user_input == "1":
                # Handle UPI adapter setup
                entered_vpa = input("  UPI VPA (e.g. user@paytm): ").strip()
                final_vpa = entered_vpa if entered_vpa else "user@upi"
                upi_adapter = UPIAdapter(vpa=final_vpa)
                print(f"  Payment method: UPI → {final_vpa}")
                return upi_adapter

            elif user_input == "2":
                # Handle Credit/Debit Card adapter setup
                entered_token = input("  Card token (e.g. VISA-1234): ").strip()
                final_token = entered_token if entered_token else "CARD-0001"
                card_adapter = CardAdapter(card_token=final_token)
                print(f"  Payment method: Card → {final_token}")
                return card_adapter

            elif user_input == "3":
                # Handle Digital Wallet adapter setup
                entered_wallet = input("  Wallet ID (e.g. WALLET-001): ").strip()
                final_wallet = entered_wallet if entered_wallet else "WALLET-001"
                wallet_adapter = DigitalWalletAdapter(wallet_id=final_wallet)
                print(f"  Payment method: Wallet → {final_wallet}")
                return wallet_adapter

            else:
                # Catch-all for invalid numeric inputs
                print("  Invalid choice. Enter 0, 1, 2, or 3.")
