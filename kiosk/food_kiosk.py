"""
File: kiosks/food_kiosk.py
Purpose: FoodKiosk — extends base Kiosk with food-specific behaviour.
         Demonstrates Inheritance from the base Kiosk class.
"""

from core.kiosk import Kiosk


class FoodKiosk(Kiosk):
    """
    Food/Metro kiosk.
    Inherits base Kiosk and adds food safety and daily limit logic.
    """

    def __init__(self, kiosk_id: str, location: str):
        super().__init__(kiosk_id, location, kiosk_type="FoodKiosk")
        self._daily_purchase_limit = 10     # max items per user per day
        self._user_purchase_counts = {}     # user_id → count today

    def can_user_purchase(self, user_id: str) -> bool:
        """Check if the user has not exceeded their daily purchase limit."""
        count = self._user_purchase_counts.get(user_id, 0)
        return count < self._daily_purchase_limit

    def record_purchase(self, user_id: str):
        self._user_purchase_counts[user_id] = (
            self._user_purchase_counts.get(user_id, 0) + 1
        )

    def get_purchase_count(self, user_id: str) -> int:
        return self._user_purchase_counts.get(user_id, 0)

    def display_info(self):
        super().display_info()
        print(f"  Daily purchase limit: {self._daily_purchase_limit} items/user")
