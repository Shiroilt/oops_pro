"""
DESIGN PATTERN: Decorator
File: hardware/dispenser.py

Purpose:
This module defines the base hardware of the kiosk and allows
optional hardware features (like fridge, solar, network)
to be added dynamically without modifying the base class.
"""

from abc import ABC, abstractmethod


# ───────────────────────── ABSTRACT COMPONENT ───────────────────────── #

class KioskHardware(ABC):
    """
    Common interface for all hardware components.
    Both base hardware and decorators follow this.
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


# ─────────────────────── BASE HARDWARE (CORE) ─────────────────────── #

class BaseDispenser(KioskHardware):
    """
    Main kiosk hardware (core system).
    Handles dispensing + basic motor operations.
    """

    def __init__(self, kiosk_id: str):
        self.kiosk_id = kiosk_id
        self._is_dispenser_ok = True
        self._is_motor_ok = True

    def get_status(self) -> str:
        return f"Kiosk [{self.kiosk_id}] — Dispenser: OK | Motor: OK"

    def get_capabilities(self) -> list:
        return ["dispenser", "motor", "basic_power"]

    def run_diagnostics(self) -> dict:
        return {
            "kiosk_id": self.kiosk_id,
            "dispenser": "OK" if self._is_dispenser_ok else "FAULT",
            "motor": "OK" if self._is_motor_ok else "FAULT",
        }

    def dispense(self, item_name: str):
        print(f"  [Dispenser] Dispensing item: {item_name}")


# ─────────────────────── DECORATOR BASE CLASS ─────────────────────── #

class HardwareDecorator(KioskHardware):
    """
    Base decorator class.
    Wraps existing hardware and extends functionality.
    """

    def __init__(self, hardware: KioskHardware):
        self._wrapped_hw = hardware

    def get_status(self) -> str:
        return self._wrapped_hw.get_status()

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities()

    def run_diagnostics(self) -> dict:
        return self._wrapped_hw.run_diagnostics()


# ─────────────────────── DECORATOR: FRIDGE ───────────────────────── #

class RefrigerationModule(HardwareDecorator):
    """
    Adds refrigeration support to hardware.
    Useful for food/pharma kiosks.
    """

    def __init__(self, hardware: KioskHardware, target_temp_c: float = 4.0):
        super().__init__(hardware)
        self.target_temp_c = target_temp_c
        self._current_temp_c = target_temp_c + 0.3

    def get_status(self) -> str:
        return (f"{self._wrapped_hw.get_status()} | "
                f"Fridge: {self._current_temp_c:.1f}C (target {self.target_temp_c}C)")

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["refrigeration"]

    def run_diagnostics(self) -> dict:
        diag_data = self._wrapped_hw.run_diagnostics()
        diag_data["refrigeration"] = {
            "status": "OK",
            "current_temp_c": self._current_temp_c,
            "target_temp_c": self.target_temp_c,
        }
        return diag_data

    def is_temp_safe(self) -> bool:
        return abs(self._current_temp_c - self.target_temp_c) < 2.0


# ─────────────────────── DECORATOR: SOLAR ───────────────────────── #

class SolarModule(HardwareDecorator):
    """
    Adds solar power monitoring capability.
    """

    def __init__(self, hardware: KioskHardware):
        super().__init__(hardware)
        self._solar_output_watts = 85.0

    def get_status(self) -> str:
        return f"{self._wrapped_hw.get_status()} | Solar: {self._solar_output_watts}W"

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["solar_power"]

    def run_diagnostics(self) -> dict:
        diag_data = self._wrapped_hw.run_diagnostics()
        diag_data["solar"] = {
            "output_watts": self._solar_output_watts,
            "status": "OK"
        }
        return diag_data


# ─────────────────────── DECORATOR: NETWORK ───────────────────────── #

class NetworkModule(HardwareDecorator):
    """
    Adds network connectivity monitoring.
    """

    def __init__(self, hardware: KioskHardware, ssid: str = "CityNet"):
        super().__init__(hardware)
        self._network_name = ssid
        self._signal_strength_dbm = -62

    def get_status(self) -> str:
        return (f"{self._wrapped_hw.get_status()} | "
                f"Network: {self._network_name} ({self._signal_strength_dbm} dBm)")

    def get_capabilities(self) -> list:
        return self._wrapped_hw.get_capabilities() + ["network"]

    def run_diagnostics(self) -> dict:
        diag_data = self._wrapped_hw.run_diagnostics()
        diag_data["network"] = {
            "ssid": self._network_name,
            "signal_dBm": self._signal_strength_dbm,
            "connected": self._signal_strength_dbm > -80,
        }
        return diag_data