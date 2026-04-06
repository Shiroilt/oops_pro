"""
File: inventory/product.py
Purpose: Represents a single sellable product in the kiosk inventory.
Demonstrates: Encapsulation — stock, price, and reservation are managed internally.
"""


class Product:
    """
    Leaf-level inventory item.
    Encapsulates stock management, pricing, and availability logic.
    """

    def __init__(self, product_id: str, name: str, price: float,
                 stock: int, requires_refrigeration: bool = False):
        self.product_id = product_id
        self.name = name
        self._price = price
        self._stock = stock
        self._reserved = 0
        self.requires_refrigeration = requires_refrigeration

    # ── InventoryItem interface methods ───────────────────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        return self._price

    def get_available_stock(self) -> int:
        return max(0, self._stock - self._reserved)

    def is_available(self) -> bool:
        return self.get_available_stock() > 0

    # ── Stock Operations ──────────────────────────────────────────────────────

    def reserve(self):
        """Temporarily hold one unit during an active transaction."""
        if self._reserved < self._stock:
            self._reserved += 1

    def release_reservation(self):
        """Release a reservation if a transaction is cancelled."""
        self._reserved = max(0, self._reserved - 1)

    def confirm_sale(self):
        """Permanently reduce stock when a purchase completes."""
        if self._stock > 0:
            self._stock -= 1
            self._reserved = max(0, self._reserved - 1)

    def restock(self, quantity: int):
        self._stock += quantity

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix = "  " * indent
        fridge = " [CHILLED]" if self.requires_refrigeration else ""
        print(f"{prefix}[Product] {self.name}{fridge} "
              f"— Rs.{self._price:.2f} | Stock: {self.get_available_stock()}")

    def __str__(self):
        return f"Product({self.product_id}, {self.name}, Rs.{self._price}, stock={self._stock})"
