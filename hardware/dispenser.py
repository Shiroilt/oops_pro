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


    def get_status(self) -> str:
        health = "OK" if self.is_healthy() else "FAULT"
        return f"Dispenser:{health} Motor:{health}"

    def get_capabilities(self) -> list:
        return ["dispenser", "motor", "basic_power"]

    def run_diagnostics(self) -> dict:
        return {
            "kiosk_id":  self.kiosk_id,
            "dispenser": "OK" if self._dispenser_ok else "FAULT",
            "motor":     "OK" if self._motor_ok     else "FAULT",
        }

    def is_healthy(self) -> bool:
        return self._dispenser_ok and self._motor_ok

    def simulate_fault(self):
        self._dispenser_ok = False
        print(f"  [Hardware] Dispenser fault simulated on {self.kiosk_id}")

    def to_dict(self) -> dict:
        return {"type": "base", "kiosk_id": self.kiosk_id}


# ── Abstract Decorator ────────────────────────────────────────────────────────

class HardwareDecorator(KioskHardware):
    """
    DECORATOR BASE: Wraps any KioskHardware and delegates all calls.
    Subclasses override only what they extend.
    """

    def __init__(self, hardware: KioskHardware):
        self._hardware = hardware

    def get_status(self) -> str:
        return self._hardware.get_status()

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities()

    def run_diagnostics(self) -> dict:
        return self._hardware.run_diagnostics()

    def is_healthy(self) -> bool:
        return self._hardware.is_healthy()


# ── Concrete Decorators ───────────────────────────────────────────────────────

class RefrigerationModule(HardwareDecorator):
    """DECORATOR: Adds refrigeration capability to any hardware stack."""

    def __init__(self, hardware: KioskHardware, target_temp_c: float = 4.0):
        super().__init__(hardware)
        self.target_temp_c   = target_temp_c
        self._current_temp   = target_temp_c + 0.3
        self._ok             = True

    def get_status(self) -> str:
        return (f"{self._hardware.get_status()} | "
                f"Fridge:{self._current_temp:.1f}°C")

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["refrigeration"]

    def run_diagnostics(self) -> dict:
        d = self._hardware.run_diagnostics()
        d["refrigeration"] = {
            "status":   "OK" if self._ok else "FAULT",
            "temp_c":   self._current_temp,
            "target_c": self.target_temp_c,
        }
        return d

    def is_healthy(self) -> bool:
        return self._hardware.is_healthy() and self._ok


class SolarModule(HardwareDecorator):
    """DECORATOR: Adds solar power monitoring to any hardware stack."""

    def __init__(self, hardware: KioskHardware):
        super().__init__(hardware)
        self._output_w = 85.0

    def get_status(self) -> str:
        return f"{self._hardware.get_status()} | Solar:{self._output_w}W"

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["solar_power"]

    def run_diagnostics(self) -> dict:
        d = self._hardware.run_diagnostics()
        d["solar"] = {"output_watts": self._output_w, "status": "OK"}
        return d

    def is_healthy(self) -> bool:
        return self._hardware.is_healthy()


class NetworkModule(HardwareDecorator):
    """DECORATOR: Adds network connectivity monitoring to any hardware stack."""

    def __init__(self, hardware: KioskHardware, ssid: str = "CityNet"):
        super().__init__(hardware)
        self._ssid      = ssid
        self._signal    = -62
        self._connected = True

    def get_status(self) -> str:
        return (f"{self._hardware.get_status()} | "
                f"Net:{self._ssid}({'OK' if self._connected else 'DOWN'})")

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["network"]

    def run_diagnostics(self) -> dict:
        d = self._hardware.run_diagnostics()
        d["network"] = {
            "ssid":       self._ssid,
            "signal_dBm": self._signal,
            "connected":  self._connected,
        }
        return d

    def is_healthy(self) -> bool:
        return self._hardware.is_healthy() and self._connected
