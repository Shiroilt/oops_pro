"""
File: kiosks/pharmacy_kiosk.py
Purpose: PharmacyKiosk — extends base Kiosk with pharmacy-specific behaviour.
         Demonstrates Inheritance from the base Kiosk class.
"""

from core.kiosk import Kiosk


class PharmacyKiosk(Kiosk):
    """
    Pharmacy-specific kiosk.
    Inherits base Kiosk and adds prescription verification logic.
    """

    def __init__(self, kiosk_id: str, location: str):
        super().__init__(kiosk_id, location, kiosk_type="PharmacyKiosk")
        self._prescription_required = True
        self._verified_users = set()

    def verify_prescription(self, user_id: str, prescription_code: str) -> bool:
        """
        Pharmacy-specific: verify a user's prescription before allowing purchase.
        In a real system this would validate against a hospital database.
        """
        # Simulated: any non-empty code is valid
        if prescription_code and len(prescription_code) >= 4:
            self._verified_users.add(user_id)
            print(f"  [PharmacyKiosk] Prescription verified for user {user_id}")
            return True
        print(f"  [PharmacyKiosk] Invalid prescription for user {user_id}")
        return False

    def is_user_verified(self, user_id: str) -> bool:
        return user_id in self._verified_users

    def display_info(self):
        super().display_info()
        print(f"  Prescription required : {self._prescription_required}")
        print(f"  Verified users        : {len(self._verified_users)}")
