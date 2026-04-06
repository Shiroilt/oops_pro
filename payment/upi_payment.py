"""
File: payment/upi_payment.py
Purpose: Simulates an existing third-party UPI payment system.
         This class has its OWN incompatible API — it is the ADAPTEE.
         The kiosk cannot use this directly; it needs an Adapter.
"""


class UPISystemAPI:
    """
    Third-party UPI payment system with its own incompatible API.
    ADAPTEE in the Adapter pattern.
    """

    def initiate_upi_payment(self, vpa: str, rupees: float) -> bool:
        """UPI-specific method — not compatible with PaymentProcessor interface."""
        print(f"  [UPI API] Initiating payment of Rs.{rupees:.2f} to VPA: {vpa}")
        return True

    def upi_refund(self, vpa: str, rupees: float) -> bool:
        """UPI-specific refund method."""
        print(f"  [UPI API] Refunding Rs.{rupees:.2f} to VPA: {vpa}")
        return True

    def check_upi_status(self, vpa: str) -> str:
        """UPI-specific status check."""
        return "ACTIVE"
