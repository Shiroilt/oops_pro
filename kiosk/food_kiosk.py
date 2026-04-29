"""
File: kiosk/food_kiosk.py
Purpose: FoodKiosk — daily purchase limit per user.
         Inherits from base Kiosk; overrides can_user_purchase().
"""
from core.kiosk import Kiosk


class FoodKiosk(Kiosk):
    """Food kiosk for metro/campus. Allows up to daily_limit items per user."""

    def __init__(self, kiosk_id: str, location: str, password: str = "1234"):
        super().__init__(kiosk_id, location, "FoodKiosk", password)
        self._daily_limit = 10

    def can_user_purchase(self, user_id: str) -> bool:
        if self._emergency_mode:
            return super().can_user_purchase(user_id)
        return self._user_purchase_counts.get(user_id, 0) < self._daily_limit

    def display_info(self):
        super().display_info()
        print(f"  Daily limit : {self._daily_limit} items/user")
