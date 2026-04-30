"""
File: kiosk/food_kiosk.py
Purpose: Specialized kiosk for food items with a per-user daily purchase limit.

         Extends the base Kiosk class and customizes purchase rules
         for normal (non-emergency) operation.
"""

from core.kiosk import Kiosk


class FoodKiosk(Kiosk):
    """
    Represents a food vending kiosk (e.g., metro stations, campuses).

    Rules:
    - Each user can purchase up to a fixed number of items per day
    - In emergency mode, base class rules are applied instead
    """

    def __init__(self, kiosk_id: str, location: str, password: str = "1234"):
        super().__init__(kiosk_id, location, "FoodKiosk", password)
        self._max_daily_items = 10  # per-user purchase limit

    def can_user_purchase(self, user_id: str) -> bool:
        """
        Determines whether a user is allowed to make a purchase.
        """
        if self._emergency_mode:
            return super().can_user_purchase(user_id)

        current_count = self._user_purchase_counts.get(user_id, 0)
        return current_count < self._max_daily_items

    def display_info(self):
        """
        Display kiosk details along with purchase constraints.
        """
        super().display_info()
        print(f"  Daily limit : {self._max_daily_items} items/user")