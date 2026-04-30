"""
DESIGN PATTERN: Composite (Leaf)
File: product/product.py
Purpose: Represents a single sellable item.

         Acts as a leaf node in the Composite structure.
         Handles pricing, stock management, reservation, and hardware constraints.
"""


class Product:
    """
    COMPOSITE LEAF:
    Represents an individual product in the inventory system.

    Responsibilities:
    - Maintain stock and reservation counts
    - Provide pricing details
    - Enforce hardware dependency (e.g., refrigeration)
    """

    def __init__(self, product_id: str, name: str, price: float,
                 stock: int, requires_refrigeration: bool = False):
        self.product_id              = product_id
        self.name                    = name
        self._unit_price             = price
        self._total_stock            = stock
        self._reserved_units         = 0
        self._is_hw_unavailable      = False
        self.requires_refrigeration  = requires_refrigeration

    # ── Composite Interface (consistent with Bundle) ──────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        return self._unit_price

    def get_available_stock(self) -> int:
        """
        Derived stock:
        total stock minus reserved units.
        Returns 0 if required hardware is unavailable.
        """
        if self._is_hw_unavailable:
            return 0
        return max(0, self._total_stock - self._reserved_units)

    def is_available(self) -> bool:
        return self.get_available_stock() > 0 and not self._is_hw_unavailable

    # ── Hardware Dependency ───────────────────────────────────────────────────

    def mark_hardware_unavailable(self, flag: bool):
        """
        Set hardware availability state (e.g., no refrigeration present).
        """
        self._is_hw_unavailable = flag

    # ── Stock Operations ──────────────────────────────────────────────────────

    def reserve(self):
        if self._reserved_units < self._total_stock:
            self._reserved_units += 1

    def release_reservation(self):
        self._reserved_units = max(0, self._reserved_units - 1)

    def confirm_sale(self):
        if self._total_stock > 0:
            self._total_stock -= 1
            self._reserved_units = max(0, self._reserved_units - 1)

    def restock(self, quantity: int):
        self._total_stock += quantity

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "product_id":             self.product_id,
            "name":                   self.name,
            "price":                  self._unit_price,
            "stock":                  self._total_stock,
            "requires_refrigeration": self.requires_refrigeration,
        }

    @staticmethod
    def from_dict(data: dict) -> "Product":
        return Product(
            product_id=data["product_id"],
            name=data["name"],
            price=data["price"],
            stock=data["stock"],
            requires_refrigeration=data.get("requires_refrigeration", False),
        )

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix = "  " * indent
        fridge_tag = " [CHILLED]" if self.requires_refrigeration else ""
        hw_flag = " [UNAVAILABLE - no fridge]" if self._is_hw_unavailable else ""

        print(
            f"{prefix}[Product] {self.name}{fridge_tag}{hw_flag} "
            f"— Rs.{self._unit_price:.2f} | Stock: {self.get_available_stock()}"
        )

    def __str__(self):
        return f"Product({self.product_id}, {self.name}, Rs.{self._unit_price})"