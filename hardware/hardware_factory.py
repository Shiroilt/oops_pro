"""
DESIGN PATTERN: Factory Method (stub for final submission)
File: hardware/hardware_factory.py
Purpose: Creates pre-configured hardware setups for different kiosk types.
         Encapsulates the decorator stacking logic in one place.
"""

from hardware.dispenser import (
    BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
)
from hardware.sensor import SensorArray


class HardwareFactory:
    """
    Factory that builds pre-configured hardware stacks for each kiosk type.
    Clients receive a fully decorated KioskHardware without knowing the details.
    """

    @staticmethod
    def create_food_kiosk_hardware(kiosk_id: str):
        """
        Food kiosk needs: refrigeration + solar + network.
        Returns a fully decorated hardware stack.
        """
        base = BaseDispenser(kiosk_id)
        with_fridge = RefrigerationModule(base, target_temp_c=4.0)
        with_solar = SolarModule(with_fridge)
        with_network = NetworkModule(with_solar, ssid="MetroNet")
        sensors = SensorArray(kiosk_id)
        print(f"[HardwareFactory] Food kiosk hardware built for {kiosk_id}")
        return with_network, sensors

    @staticmethod
    def create_pharmacy_kiosk_hardware(kiosk_id: str):
        """
        Pharmacy kiosk needs: refrigeration (for medicines) + network.
        """
        base = BaseDispenser(kiosk_id)
        with_fridge = RefrigerationModule(base, target_temp_c=2.0)
        with_network = NetworkModule(with_fridge, ssid="HospitalNet")
        sensors = SensorArray(kiosk_id)
        print(f"[HardwareFactory] Pharmacy kiosk hardware built for {kiosk_id}")
        return with_network, sensors

    @staticmethod
    def create_emergency_kiosk_hardware(kiosk_id: str):
        """
        Emergency kiosk needs: solar (for off-grid power) + network.
        No refrigeration — distributes non-perishable supplies.
        """
        base = BaseDispenser(kiosk_id)
        with_solar = SolarModule(base)
        with_network = NetworkModule(with_solar, ssid="EmergencyNet")
        sensors = SensorArray(kiosk_id)
        print(f"[HardwareFactory] Emergency kiosk hardware built for {kiosk_id}")
        return with_network, sensors

    @staticmethod
    def create_basic_hardware(kiosk_id: str):
        """Minimal hardware — no optional modules."""
        base = BaseDispenser(kiosk_id)
        sensors = SensorArray(kiosk_id)
        print(f"[HardwareFactory] Basic hardware built for {kiosk_id}")
        return base, sensors
