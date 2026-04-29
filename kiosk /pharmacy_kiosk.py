"""
File: kiosk/pharmacy_kiosk.py
Purpose: PharmacyKiosk — supports optional prescription verification.
         Inherits from base Kiosk.
"""
from core.kiosk import Kiosk


class PharmacyKiosk(Kiosk):
    """Hospital-grade kiosk. Supports prescription verification module."""

    def __init__(self, kiosk_id: str, location: str, password: str = "1234"):
        super().__init__(kiosk_id, location, "PharmacyKiosk", password)
        self._verified_users: set = set()

    def verify_prescription(self, user_id: str, code: str) -> bool:
        """Verify a prescription code (must be 4+ characters)."""
        if code and len(code) >= 4:
            self._verified_users.add(user_id)
            print(f"  [PharmacyKiosk] Prescription verified for {user_id}")
            return True
        print(f"  [PharmacyKiosk] Invalid prescription code")
        return False

    def is_user_verified(self, user_id: str) -> bool:
        return user_id in self._verified_users

    def display_info(self):
        super().display_info()
        print(f"  Verified users: {len(self._verified_users)}")
