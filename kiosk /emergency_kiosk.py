"""
File: kiosk/emergency_kiosk.py
Purpose: EmergencyKiosk — strict per-person collection limits.
         Starts in emergency mode immediately.
         Inherits from base Kiosk.
"""
from core.kiosk import Kiosk


class EmergencyKiosk(Kiosk):
    """Disaster-zone kiosk. Emergency mode on by default. Strict per-person limits."""

    def __init__(self, kiosk_id: str, location: str, password: str = "1234"):
        super().__init__(kiosk_id, location, "EmergencyKiosk", password)
        self._limit_per_person = 3
        self._emergency_mode   = True      # always in emergency mode

    def can_user_purchase(self, user_id: str) -> bool:
        collected = self._user_purchase_counts.get(user_id, 0)
        return collected < self._limit_per_person
