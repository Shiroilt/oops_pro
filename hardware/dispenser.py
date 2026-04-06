"""
DESIGN PATTERN: Decorator
File: hardware/dispenser.py
Purpose: Base kiosk hardware + optional hardware modules that can be
         stacked dynamically without modifying the base class.
"""

from abc import ABC, abstractmethod


# ── Abstract Component ────────────────────────────────────────────────────────

class KioskHardware(ABC):
    """
    Abstract component interface.
    All base hardware and all decorators implement this.
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


# ── Concrete Base Component ───────────────────────────────────────────────────

class BaseDispenser(KioskHardware):
    """
    Core kiosk hardware — motor dispenser + basic sensors.
    This is the base component that decorators wrap around.
    """

    def __init__(self, kiosk_id: str):
        self.kiosk_id = kiosk_id
        self._dispenser_ok = True
        self._motor_ok = True

    def get_status(self) -> str:
        return f"Kiosk [{self.kiosk_id}] — Dispenser: OK | Motor: OK"

    def get_capabilities(self) -> list:
        return ["dispenser", "motor", "basic_power"]

    def run_diagnostics(self) -> dict:
        return {
            "kiosk_id": self.kiosk_id,
            "dispenser": "OK" if self._dispenser_ok else "FAULT",
            "motor": "OK" if self._motor_ok else "FAULT",
        }

    def dispense(self, item_name: str):
        print(f"  [Dispenser] Dispensing: {item_name}")


# ── Decorator Base ────────────────────────────────────────────────────────────

class HardwareDecorator(KioskHardware):
    """
    Base decorator — wraps any KioskHardware and delegates by default.
    Subclasses override only the methods they extend.
    """

    def __init__(self, hardware: KioskHardware):
        self._hardware = hardware

    def get_status(self) -> str:
        return self._hardware.get_status()

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities()

    def run_diagnostics(self) -> dict:
        return self._hardware.run_diagnostics()


# ── Concrete Decorators (Optional Hardware Modules) ───────────────────────────

class RefrigerationModule(HardwareDecorator):
    """
    DECORATOR: Adds refrigeration capability to any kiosk hardware.
    Can be wrapped around BaseDispenser or another decorator.
    """

    def __init__(self, hardware: KioskHardware, target_temp_c: float = 4.0):
        super().__init__(hardware)
        self.target_temp_c = target_temp_c
        self._current_temp = target_temp_c + 0.3   # slight variance

    def get_status(self) -> str:
        return (f"{self._hardware.get_status()} | "
                f"Fridge: {self._current_temp:.1f}C (target {self.target_temp_c}C)")

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["refrigeration"]

    def run_diagnostics(self) -> dict:
        diag = self._hardware.run_diagnostics()
        diag["refrigeration"] = {
            "status": "OK",
            "current_temp_c": self._current_temp,
            "target_temp_c": self.target_temp_c,
        }
        return diag

    def is_temp_safe(self) -> bool:
        return abs(self._current_temp - self.target_temp_c) < 2.0


class SolarModule(HardwareDecorator):
    """
    DECORATOR: Adds solar power monitoring to any kiosk hardware.
    """

    def __init__(self, hardware: KioskHardware):
        super().__init__(hardware)
        self._output_watts = 85.0

    def get_status(self) -> str:
        return f"{self._hardware.get_status()} | Solar: {self._output_watts}W"

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["solar_power"]

    def run_diagnostics(self) -> dict:
        diag = self._hardware.run_diagnostics()
        diag["solar"] = {"output_watts": self._output_watts, "status": "OK"}
        return diag


class NetworkModule(HardwareDecorator):
    """
    DECORATOR: Adds network connectivity monitoring to any kiosk hardware.
    """

    def __init__(self, hardware: KioskHardware, ssid: str = "CityNet"):
        super().__init__(hardware)
        self._ssid = ssid
        self._signal_dbm = -62

    def get_status(self) -> str:
        return (f"{self._hardware.get_status()} | "
                f"Network: {self._ssid} ({self._signal_dbm} dBm)")

    def get_capabilities(self) -> list:
        return self._hardware.get_capabilities() + ["network"]

    def run_diagnostics(self) -> dict:
        diag = self._hardware.run_diagnostics()
        diag["network"] = {
            "ssid": self._ssid,
            "signal_dBm": self._signal_dbm,
            "connected": self._signal_dbm > -80,
        }
        return diag
