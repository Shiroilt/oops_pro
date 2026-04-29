"""
DESIGN PATTERN: Decorator (Structural)
File: hardware/dispenser.py
Purpose: Base hardware + optional modules stacked dynamically at runtime.
         Each module (Refrigeration, Solar, Network) is a Decorator that
         wraps and extends the hardware beneath it.
         Hardware health affects kiosk operational status.

Decorator chain example:
  BaseDispenser
    → RefrigerationModule(base)
      → SolarModule(fridge)
        → NetworkModule(solar)   ← outer hardware used by kiosk
"""

from abc import ABC, abstractmethod


# ── Abstract Component ────────────────────────────────────────────────────────

class KioskHardware(ABC):
    """Abstract component — BaseDispenser and all Decorators implement this."""

    @abstractmethod
    def get_status(self) -> str:
        pass

    @abstractmethod
    def get_capabilities(self) -> list:
        pass

    @abstractmethod
    def run_diagnostics(self) -> dict:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass


# ── Concrete Base Component ───────────────────────────────────────────────────

class BaseDispenser(KioskHardware):
    """Concrete component — core kiosk dispenser hardware."""

    def __init__(self, kiosk_id: str):
        self.kiosk_id      = kiosk_id
        self._dispenser_ok = True
        self._motor_ok     = True
