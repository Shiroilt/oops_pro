"""
File: kiosks/emergency_kiosk.py
Purpose: EmergencyReliefKiosk — extends base Kiosk with emergency-specific behaviour.
         Demonstrates Inheritance from the base Kiosk class.
"""

from core.kiosk import Kiosk


class EmergencyKiosk(Kiosk):
    """
    Emergency relief kiosk.
    Inherits base Kiosk and enforces emergency purchase limits per household.
    """

    def __init__(self, kiosk_id: str, location: str):
        super().__init__(kiosk_id, location, kiosk_type="EmergencyKiosk")
        self._emergency_limit_per_user = 3      # max items per person in emergency
        self._household_distribution = {}        # user_id → items collected

    def activate_emergency_mode(self):
        self.set_mode("ACTIVE")
        print(f"  [EmergencyKiosk {self.kiosk_id}] EMERGENCY MODE ACTIVATED")
        print(f"  Per-person limit set to {self._emergency_limit_per_user} items")

    def can_collect(self, user_id: str) -> bool:
        """Check whether this user can still collect items."""
        collected = self._household_distribution.get(user_id, 0)
        return collected < self._emergency_limit_per_user

    def record_collection(self, user_id: str):
        self._household_distribution[user_id] = (
            self._household_distribution.get(user_id, 0) + 1
        )

    def remaining_allowance(self, user_id: str) -> int:
        collected = self._household_distribution.get(user_id, 0)
        return max(0, self._emergency_limit_per_user - collected)

    def display_info(self):
        super().display_info()
        print(f"  Emergency limit : {self._emergency_limit_per_user} items/person")
        print(f"  Households served: {len(self._household_distribution)}")
