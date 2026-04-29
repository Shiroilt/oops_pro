"""
DESIGN PATTERN: Composite (Leaf)
File: product/product.py
Purpose: Single sellable product. Leaf node in the Composite tree.
         Encapsulates stock, pricing, reservation, hardware dependency.
"""


class Product:
    """
    COMPOSITE LEAF: Single inventory item.
    Encapsulation: stock, price, reservation all managed internally.
    Hardware dependency: chilled items unavailable without fridge module.
    """

    def __init__(self, product_id: str, name: str, price: float,
                 stock: int, requires_refrigeration: bool = False):
        self.product_id            = product_id
        self.name                  = name
        self._base_price           = price
        self._stock                = stock
        self._reserved             = 0
        self._hardware_unavailable = False
        self.requires_refrigeration = requires_refrigeration

    # ── Interface (matches Bundle interface for Composite) ────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        return self._base_price

    def get_available_stock(self) -> int:
        """Derived: stock minus reserved, zero if hardware missing."""
        if self._hardware_unavailable:
            return 0
        return max(0, self._stock - self._reserved)

    def is_available(self) -> bool:
        return self.get_available_stock() > 0 and not self._hardware_unavailable

    # ── Hardware dependency ───────────────────────────────────────────────────

    def mark_hardware_unavailable(self, unavailable: bool):
        """Called by Inventory when required hardware module is missing."""
        self._hardware_unavailable = unavailable

    # ── Stock operations ──────────────────────────────────────────────────────

    def reserve(self):
        if self._reserved < self._stock:
            self._reserved += 1

    def release_reservation(self):
        self._reserved = max(0, self._reserved - 1)

    def confirm_sale(self):
        if self._stock > 0:
            self._stock -= 1
            self._reserved = max(0, self._reserved - 1)

    def restock(self, quantity: int):
        self._stock += quantity

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "product_id":             self.product_id,
            "name":                   self.name,
            "price":                  self._base_price,
            "stock":                  self._stock,
            "requires_refrigeration": self.requires_refrigeration,
        }

    @staticmethod
    def from_dict(d: dict) -> "Product":
        return Product(
            product_id=d["product_id"],
            name=d["name"],
            price=d["price"],
            stock=d["stock"],
            requires_refrigeration=d.get("requires_refrigeration", False),
        )

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix  = "  " * indent
        fridge  = " [CHILLED]" if self.requires_refrigeration else ""
        unavail = " [UNAVAILABLE - no fridge]" if self._hardware_unavailable else ""
        print(f"{prefix}[Product] {self.name}{fridge}{unavail} "
              f"— Rs.{self._base_price:.2f} | Stock: {self.get_available_stock()}")

    def __str__(self):
        return f"Product({self.product_id}, {self.name}, Rs.{self._base_price})"
