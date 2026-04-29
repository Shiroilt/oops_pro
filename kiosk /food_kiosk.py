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

