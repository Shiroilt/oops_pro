"""
DESIGN PATTERN: Composite (Branch/Composite node)
File: product/bundle.py
Purpose: ProductBundle contains Products or other Bundles.
         Price, stock, availability resolve recursively through the tree.
         Purchasing a bundle deducts ALL contained items atomically.
"""


class ProductBundle:
    """
    COMPOSITE BRANCH: Treats a group of items as one inventory item.
    Supports nested bundles (bundles inside bundles — recursive tree).
    """

    def __init__(self, bundle_id: str, name: str, discount_pct: float = 0.0):
        self.bundle_id   = bundle_id
        self.name        = name
        self.discount_pct = discount_pct
        self._items      = []
        self.requires_refrigeration = False

    def add_item(self, item):
        self._items.append(item)
        if getattr(item, 'requires_refrigeration', False):
            self.requires_refrigeration = True

    # ── Composite interface (same as Product) ─────────────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> float:
        """Price = sum of children with discount applied."""
        total = sum(item.get_price() for item in self._items)
        return round(total * (1 - self.discount_pct / 100), 2)

    def get_available_stock(self) -> int:
        """Available = minimum stock across all children (bottleneck)."""
        if not self._items:
            return 0
        return min(item.get_available_stock() for item in self._items)

    def is_available(self) -> bool:
        return self.get_available_stock() > 0 and all(
            item.is_available() for item in self._items
        )

    # ── Stock operations ──────────────────────────────────────────────────────

    def reserve(self):
        for item in self._items:
            item.reserve()

    def release_reservation(self):
        for item in self._items:
            item.release_reservation()

    def confirm_sale(self):
        """Deduct stock from ALL contained items atomically."""
        for item in self._items:
            item.confirm_sale()

    def restock(self, quantity: int):
        for item in self._items:
            if hasattr(item, 'restock'):
                item.restock(quantity)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "bundle_id":    self.bundle_id,
            "name":         self.name,
            "discount_pct": self.discount_pct,
            "items":        [item.to_dict() if hasattr(item, 'to_dict') else {}
                             for item in self._items],
            "type":         "bundle",
        }

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}[Bundle] {self.name} — Rs.{self.get_price():.2f} "
              f"({self.discount_pct}% off) | Stock: {self.get_available_stock()}")
        for item in self._items:
            item.display(indent + 1)
