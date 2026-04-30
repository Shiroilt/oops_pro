"""
DESIGN PATTERN: Decorator (Structural)
File: hardware/dispenser.py
Purpose: Defines base hardware and allows dynamic extension using decorators.

         Modules like Refrigeration, Solar, and Network wrap around base hardware
         and extend functionality without modifying existing classes.

         Hardware chain example:
           BaseDispenser
             → RefrigerationModule(base)
               → SolarModule(fridge)
                 → NetworkModule(solar)
"""

from abc import ABC, abstractmethod


# ── Abstract Component ────────────────────────────────────────────────────────

class KioskHardware(ABC):
    """
    Abstract base for all hardware components.
    Both base hardware and decorators must implement this interface.
    """

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
    """Core hardware unit representing the vending mechanism."""

    def __init__(self, kiosk_id: str):
        self.kiosk_id        = kiosk_id
        self._dispenser_ok   = True
        self._motor_ok       = True

    def get_status(self) -> str:
        state = "OK" if self.is_healthy() else "FAULT"
        return f"Dispenser:{state} Motor:{state}"

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
        print(f"  [Hardware] Fault injected into dispenser at {self.kiosk_id}")

    def to_dict(self) -> dict:
        return {"type": "base", "kiosk_id": self.kiosk_id}


# ── Abstract Decorator ────────────────────────────────────────────────────────

class HardwareDecorator(KioskHardware):
    """
    Base decorator class.
    Wraps a hardware object and forwards all method calls.
    """

    def __init__(self, wrapped_hw: KioskHardware):
        self._wrapped_hw = wrapped_hw

    def get_status(self) -> str:
        return self._wrapped_hw.get_status()

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities()

    def run_diagnostics(self) -> dict:
        return self._wrapped_hw.run_diagnostics()

    def is_healthy(self) -> bool:
        return self._wrapped_hw.is_healthy()


# ── Concrete Decorators ───────────────────────────────────────────────────────

class RefrigerationModule(HardwareDecorator):
    """Adds temperature control functionality to hardware."""

    def __init__(self, wrapped_hw: KioskHardware, target_temp_c: float = 4.0):
        super().__init__(wrapped_hw)
        self.target_temp_c  = target_temp_c
        self._current_temp  = target_temp_c + 0.3
        self._is_ok         = True

    def get_status(self) -> str:
        return (
            f"{self._wrapped_hw.get_status()} | "
            f"Fridge:{self._current_temp:.1f}°C"
        )

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["refrigeration"]

    def run_diagnostics(self) -> dict:
        report = self._wrapped_hw.run_diagnostics()
        report["refrigeration"] = {
            "status":   "OK" if self._is_ok else "FAULT",
            "temp_c":   self._current_temp,
            "target_c": self.target_temp_c,
        }
        return report

    def is_healthy(self) -> bool:
        return self._wrapped_hw.is_healthy() and self._is_ok


class SolarModule(HardwareDecorator):
    """Adds solar power monitoring capability."""

    def __init__(self, wrapped_hw: KioskHardware):
        super().__init__(wrapped_hw)
        self._power_output = 85.0

    def get_status(self) -> str:
        return f"{self._wrapped_hw.get_status()} | Solar:{self._power_output}W"

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["solar_power"]

    def run_diagnostics(self) -> dict:
        report = self._wrapped_hw.run_diagnostics()
        report["solar"] = {
            "output_watts": self._power_output,
            "status": "OK",
        }
        return report

    def is_healthy(self) -> bool:
        return self._wrapped_hw.is_healthy()


class NetworkModule(HardwareDecorator):
    """Adds network connectivity monitoring."""

    def __init__(self, wrapped_hw: KioskHardware, ssid: str = "CityNet"):
        super().__init__(wrapped_hw)
        self._ssid        = ssid
        self._signal_dbm  = -62
        self._is_connected = True

    def get_status(self) -> str:
        return (
            f"{self._wrapped_hw.get_status()} | "
            f"Net:{self._ssid}({'OK' if self._is_connected else 'DOWN'})"
        )

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["network"]

    def run_diagnostics(self) -> dict:
        report = self._wrapped_hw.run_diagnostics()
        report["network"] = {
            "ssid":       self._ssid,
            "signal_dBm": self._signal_dbm,
            "connected":  self._is_connected,
        }
        return report

    def is_healthy(self) -> bool:
        return self._wrapped_hw.is_healthy() and self._is_connected