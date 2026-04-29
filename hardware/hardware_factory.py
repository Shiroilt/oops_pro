"""
DESIGN PATTERN: Factory (Creational)
File: hardware/hardware_factory.py
Purpose: Builds pre-configured hardware stacks per kiosk type.
         Returns the fully assembled Decorator chain + SensorArray.
"""

from hardware.dispenser import (
    BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
)
from hardware.sensor import SensorArray


class HardwareFactory:
    """Factory: assembles the correct hardware decorator chain per kiosk type."""

    @staticmethod
    def create_food_kiosk_hardware(kiosk_id: str):
        """Food kiosk: fridge + solar + network."""
        base = BaseDispenser(kiosk_id)
        hw   = RefrigerationModule(base, target_temp_c=4.0)
        hw   = SolarModule(hw)
        hw   = NetworkModule(hw, ssid="MetroNet")
        return hw, SensorArray(kiosk_id)

    @staticmethod
    def create_pharmacy_kiosk_hardware(kiosk_id: str):
        """Pharmacy kiosk: fridge (medical temp) + network."""
        base = BaseDispenser(kiosk_id)
        hw   = RefrigerationModule(base, target_temp_c=2.0)
        hw   = NetworkModule(hw, ssid="HospitalNet")
        return hw, SensorArray(kiosk_id)

    @staticmethod
    def create_emergency_kiosk_hardware(kiosk_id: str):
        """Emergency kiosk: solar (off-grid) + network."""
        base = BaseDispenser(kiosk_id)
        hw   = SolarModule(base)
        hw   = NetworkModule(hw, ssid="EmergencyNet")
        return hw, SensorArray(kiosk_id)
