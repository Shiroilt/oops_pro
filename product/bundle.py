"""
DESIGN PATTERN: Composite (Composite Node / Branch)
File: product/bundle.py
Purpose: Represents a bundle that can contain multiple products
         or even nested bundles.

         Key Behavior:
         - Price is calculated recursively
         - Stock is determined by the minimum available child
         - Purchase affects all contained items atomically
"""


class ProductBundle:
    """
    COMPOSITE NODE:
    Represents a grouped product unit that behaves like a single item.

    Supports:
    - Nested bundles (tree structure)
    - Recursive price and stock calculation
    """

    def __init__(self, bundle_id: str, name: str, discount_pct: float = 0.0):
        self.bundle_id        = bundle_id
        self.name             = name
        self.discount_pct     = discount_pct
        self._children        = []
        self.requires_refrigeration = False

    def add_item(self, component):
        """
        Add a product or another bundle into this bundle.
        """
        self._children.append(component)

        # If any child requires refrigeration, bundle also requires it
        if getattr(component, 'requires_refrigeration', False):
            self.requires_refrigeration = True

    # ── Composite Interface (same behavior as Product) ─────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        """
        Total price = sum of child prices with discount applied.
        """
        total_price = sum(child.get_price() for child in self._children)
        return round(total_price * (1 - self.discount_pct / 100), 2)

    def get_available_stock(self) -> int:
        """
        Available stock = minimum stock among all children.
        """
        if not self._children:
            return 0
        return min(child.get_available_stock() for child in self._children)

    def is_available(self) -> bool:
        """
        Bundle is available only if:
        - stock > 0
        - all children are available
        """
        return self.get_available_stock() > 0 and all(
            child.is_available() for child in self._children
        )

    # ── Stock Operations ──────────────────────────────────────────────────────

    def reserve(self):
        for child in self._children:
            child.reserve()

    def release_reservation(self):
        for child in self._children:
            child.release_reservation()

    def confirm_sale(self):
        """
        Confirm purchase by deducting stock from ALL child items.
        """
        for child in self._children:
            child.confirm_sale()

    def restock(self, quantity: int):
        for child in self._children:
            if hasattr(child, 'restock'):
                child.restock(quantity)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "bundle_id":    self.bundle_id,
            "name":         self.name,
            "discount_pct": self.discount_pct,
            "items":        [
                child.to_dict() if hasattr(child, 'to_dict') else {}
                for child in self._children
            ],
            "type":         "bundle",
        }

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix = "  " * indent
        print(
            f"{prefix}[Bundle] {self.name} — Rs.{self.get_price():.2f} "
            f"({self.discount_pct}% off) | Stock: {self.get_available_stock()}"
        )
        for child in self._children:
            child.display(indent + 1)