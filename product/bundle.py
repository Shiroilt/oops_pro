"""
DESIGN PATTERN: Composite
File: inventory/bundle.py
Purpose: A ProductBundle can contain Products or other ProductBundles.
         All operations (price, stock, availability) resolve recursively.
"""

from typing import List


class ProductBundle:
    """
    COMPOSITE: Treats a group of InventoryItems as a single InventoryItem.
    Bundles can contain other bundles (nested composition).
    """

    def __init__(self, bundle_id: str, name: str, discount_pct: float = 0.0):
        self.bundle_id = bundle_id
        self.name = name
        self.discount_pct = discount_pct
        self._items: List = []          # can hold Product or ProductBundle

    # ── Composite operations ──────────────────────────────────────────────────

    def add_item(self, item):
        """Add a Product or another ProductBundle to this bundle."""
        self._items.append(item)

    def remove_item(self, item):
        self._items.remove(item)

    def get_children(self) -> list:
        return list(self._items)

    # ── InventoryItem interface methods ───────────────────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        """Recursively sum prices of all items, then apply discount."""
        total = sum(item.get_price() for item in self._items)
        return round(total * (1 - self.discount_pct / 100), 2)

    def get_available_stock(self) -> int:
        """Bundle stock = minimum stock across all contained items (recursive)."""
        if not self._items:
            return 0
        return min(item.get_available_stock() for item in self._items)

    def is_available(self) -> bool:
        return self.get_available_stock() > 0 and all(
            item.is_available() for item in self._items
        )

    def confirm_sale(self):
        """Confirm sale of one unit of every item in this bundle."""
        for item in self._items:
            item.confirm_sale()

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}[Bundle] {self.name} — Rs.{self.get_price():.2f} "
              f"({self.discount_pct}% off) | Stock: {self.get_available_stock()}")
        for item in self._items:
            item.display(indent + 1)

    def __str__(self):
        return f"Bundle({self.bundle_id}, {self.name}, {len(self._items)} items)"
