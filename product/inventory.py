"""
File: inventory/inventory.py
Purpose: Manages the full collection of products and bundles for a kiosk.
         Handles search, stock checks, and display.
"""

from inventory.product import Product
from inventory.bundle import ProductBundle


class Inventory:
    """
    Manages a list of InventoryItems (Products and Bundles).
    Acts as the central inventory store for a single kiosk.
    """

    def __init__(self):
        self._items = []

    # ── Item Management ───────────────────────────────────────────────────────

    def add_item(self, item):
        """Add a Product or ProductBundle to inventory."""
        self._items.append(item)

    def remove_item(self, item_name: str) -> bool:
        item = self.find_item(item_name)
        if item:
            self._items.remove(item)
            return True
        return False

    def get_all_items(self) -> list:
        return list(self._items)

    # ── Search ────────────────────────────────────────────────────────────────

    def find_item(self, name: str):
        """Find an item by name (case-insensitive)."""
        for item in self._items:
            if item.get_name().lower() == name.lower():
                return item
        return None

    def is_available(self, item_name: str) -> bool:
        item = self.find_item(item_name)
        return item.is_available() if item else False

    # ── Stock Operations ──────────────────────────────────────────────────────

    def restock(self, item_name: str, quantity: int) -> bool:
        item = self.find_item(item_name)
        if item and isinstance(item, Product):
            item.restock(quantity)
            print(f"[Inventory] Restocked '{item_name}' by {quantity}. "
                  f"New stock: {item.get_available_stock()}")
            return True
        print(f"[Inventory] Could not restock '{item_name}'.")
        return False

    def get_low_stock_items(self, threshold: int = 5) -> list:
        """Return items with available stock below the threshold."""
        return [item for item in self._items
                if item.get_available_stock() <= threshold]

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self):
        print("[Inventory] Current Stock:")
        if not self._items:
            print("  (empty)")
            return
        for item in self._items:
            item.display(indent=1)

    def display_low_stock(self, threshold: int = 5):
        low = self.get_low_stock_items(threshold)
        if low:
            print(f"[Inventory] WARNING — Low stock (threshold={threshold}):")
            for item in low:
                item.display(indent=1)
        else:
            print("[Inventory] All items are adequately stocked.")
