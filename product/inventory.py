"""
File: product/inventory.py
Purpose: Manages all products and bundles for a kiosk.
         Enforces hardware constraints — marks chilled items unavailable
         when refrigeration module is absent.
         Supports serialization to/from JSON.
"""

from product.product import Product
from product.bundle import ProductBundle


class Inventory:
    """
    Manages a collection of inventory items (Products and Bundles).
    Enforces hardware constraints from the kiosk's hardware stack.
    """

    def __init__(self):
        self._items = []

    # ── Item management ───────────────────────────────────────────────────────

    def add_item(self, item):
        self._items.append(item)

    def get_all_items(self) -> list:
        return list(self._items)

    def find_item(self, name: str):
        for item in self._items:
            if item.get_name().lower() == name.lower():
                return item
        return None

    # ── Hardware dependency enforcement ───────────────────────────────────────

    def enforce_hardware_constraints(self, capabilities: list):
        """
        Mark refrigerated items unavailable if fridge module is missing.
        Called automatically when hardware changes.
        """
        has_fridge = "refrigeration" in capabilities
        for item in self._items:
            if getattr(item, 'requires_refrigeration', False):
                if hasattr(item, "mark_hardware_unavailable"):
                    item.mark_hardware_unavailable(not has_fridge)

    # ── Stock operations ──────────────────────────────────────────────────────

    def restock(self, item_name: str, quantity: int) -> bool:
        item = self.find_item(item_name)
        if item and isinstance(item, Product):
            item.restock(quantity)
            return True
        return False

    def is_available(self, item_name: str) -> bool:
        item = self.find_item(item_name)
        return item.is_available() if item else False

    def get_low_stock_items(self, threshold: int = 5) -> list:
        return [item for item in self._items
                if item.get_available_stock() <= threshold]

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_list(self) -> list:
        result = []
        for item in self._items:
            if hasattr(item, 'to_dict'):
                d = item.to_dict()
                d["type"] = "bundle" if isinstance(item, ProductBundle) else "product"
                result.append(d)
        return result

    @staticmethod
    def from_list(data: list) -> "Inventory":
        inv = Inventory()
        for d in data:
            if d.get("type") == "bundle":
                bundle = ProductBundle(d["bundle_id"], d["name"],
                                       d.get("discount_pct", 0))
                for sub in d.get("items", []):
                    bundle.add_item(Product.from_dict(sub))
                inv.add_item(bundle)
            else:
                inv.add_item(Product.from_dict(d))
        return inv

    # ── Display ───────────────────────────────────────────────────────────────

    def display(self):
        print("  Current Inventory:")
        if not self._items:
            print("    (empty)")
            return
        for item in self._items:
            item.display(indent=2)
