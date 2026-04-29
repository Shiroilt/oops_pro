"""
DESIGN PATTERN: Strategy (Behavioral)
File: pricing/pricing_strategy.py
Purpose: Dynamic pricing — kiosk can switch pricing strategy at runtime
         without changing any kiosk or command code.

Strategies:
  StandardPricing   — full base price (default)
  DiscountedPricing — percentage discount (promotions)
  EmergencyPricing  — everything FREE (disaster relief)
  SurgePricing      — multiplied price (peak demand)

PricingContext holds the current strategy and delegates to it.
"""

from abc import ABC, abstractmethod


# ── Strategy Interface ────────────────────────────────────────────────────────

class PricingStrategy(ABC):
    """Abstract Strategy — all pricing policies implement this."""

    @abstractmethod
    def compute_price(self, base_price: float) -> float:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


# ── Concrete Strategies ───────────────────────────────────────────────────────

class StandardPricing(PricingStrategy):
    """Normal full price — default for all kiosks."""

    def compute_price(self, base_price: float) -> float:
        return round(base_price, 2)

    def get_name(self) -> str:
        return "Standard Pricing"


class DiscountedPricing(PricingStrategy):
    """Percentage discount — used for promotions."""

    def __init__(self, discount_pct: float = 10.0):
        self.discount_pct = discount_pct

    def compute_price(self, base_price: float) -> float:
        return round(base_price * (1 - self.discount_pct / 100), 2)

    def get_name(self) -> str:
        return f"Discounted Pricing ({self.discount_pct}% off)"


class EmergencyPricing(PricingStrategy):
    """
    Emergency/disaster mode — all items are FREE (price = 0).
    Automatically activated when emergency mode triggers.
    """

    def compute_price(self, base_price: float) -> float:
        return 0.0

    def get_name(self) -> str:
        return "Emergency Pricing (FREE)"


class SurgePricing(PricingStrategy):
    """High demand — price multiplied by surge factor."""

    def __init__(self, surge_factor: float = 1.5):
        self.surge_factor = surge_factor

    def compute_price(self, base_price: float) -> float:
        return round(base_price * self.surge_factor, 2)

    def get_name(self) -> str:
        return f"Surge Pricing (x{self.surge_factor})"


# ── Context ───────────────────────────────────────────────────────────────────

class PricingContext:
    """
    STRATEGY CONTEXT: Holds the active PricingStrategy.
    Kiosk uses this to compute prices; strategy can be swapped at runtime
    (e.g., switching to EmergencyPricing when emergency mode activates).
    """

    def __init__(self, strategy: PricingStrategy = None):
        self._strategy = strategy or StandardPricing()

    def set_strategy(self, strategy: PricingStrategy):
        print(f"  [Pricing] Strategy → {strategy.get_name()}")
        self._strategy = strategy

    def get_price(self, base_price: float) -> float:
        return self._strategy.compute_price(base_price)

    def get_strategy_name(self) -> str:
        return self._strategy.get_name()
