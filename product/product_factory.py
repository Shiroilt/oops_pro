"""
DESIGN PATTERN: Abstract Factory
File: product/product_factory.py
Purpose: Creates products belonging to the correct product family
         based on kiosk type.
         Each kiosk type defines its own product family with type-specific
         constraints (e.g., EmergencyKiosk products are always free).

Abstract Factory families:
  FoodKiosk      → FoodProduct      (regular pricing, can be chilled)
  PharmacyKiosk  → PharmacyProduct  (regular pricing, medical items)
  EmergencyKiosk → EmergencyProduct (always free/price=0)
"""

from product.product import Product


# ── Abstract Product Families ─────────────────────────────────────────────────

class FoodProduct(Product):
    """Product belonging to the Food kiosk family."""

    def display(self, indent: int = 0):
        prefix = "  " * indent
        fridge  = " [CHILLED]" if self.requires_refrigeration else ""
        unavail = " [UNAVAILABLE - no fridge]" if self._hardware_unavailable else ""
        print(f"{prefix}[Food] {self.name}{fridge}{unavail} "
              f"— Rs.{self._base_price:.2f} | Stock: {self.get_available_stock()}")


class PharmacyProduct(Product):
    """Product belonging to the Pharmacy kiosk family."""

    def display(self, indent: int = 0):
        prefix = "  " * indent
        unavail = " [UNAVAILABLE - no fridge]" if self._hardware_unavailable else ""
        print(f"{prefix}[Medicine] {self.name}{unavail} "
              f"— Rs.{self._base_price:.2f} | Stock: {self.get_available_stock()}")


class EmergencyProduct(Product):
    """
    Product belonging to the Emergency kiosk family.
    Always priced at 0 (free) regardless of input.
    """

    def __init__(self, product_id: str, name: str, price: float,
                 stock: int, requires_refrigeration: bool = False):
        super().__init__(product_id, name, 0.0, stock, requires_refrigeration)

    def display(self, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}[Relief] {self.name} "
              f"— FREE | Stock: {self.get_available_stock()}")


# ── Abstract Factory ──────────────────────────────────────────────────────────

class ProductFactory:
    """
    ABSTRACT FACTORY: Creates the correct product type for a kiosk family.
    Client code calls ProductFactory.create_product(kiosk_type, ...) and
    gets back the right product subclass — no if/else needed in calling code.
    """

    _counter = 0

    @staticmethod
    def _next_id(prefix: str) -> str:
        ProductFactory._counter += 1
        return f"{prefix}{ProductFactory._counter:03d}"

    @staticmethod
    def create_product(kiosk_type: str, name: str, price: float,
                       stock: int,
                       requires_refrigeration: bool = False) -> Product:
        """
        Factory method — returns the correct product family subclass
        based on kiosk_type.
        """
        if kiosk_type == "FoodKiosk":
            pid = ProductFactory._next_id("F")
            return FoodProduct(pid, name, price, stock, requires_refrigeration)

        elif kiosk_type == "PharmacyKiosk":
            pid = ProductFactory._next_id("M")
            return PharmacyProduct(pid, name, price, stock, requires_refrigeration)

        elif kiosk_type == "EmergencyKiosk":
            pid = ProductFactory._next_id("E")
            return EmergencyProduct(pid, name, 0.0, stock, requires_refrigeration)

        else:
            # Default fallback
            pid = ProductFactory._next_id("X")
            return Product(pid, name, price, stock, requires_refrigeration)
