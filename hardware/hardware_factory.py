"""
DESIGN PATTERN: Factory Method
File: hardware/hardware_factory.py

Purpose:
This module creates ready-to-use hardware setups for different kiosk types.
It centralizes how hardware decorators are combined, so other parts of the
system don’t need to worry about configuration details.
"""

from hardware.dispenser import (
    BaseDispenser, RefrigerationModule, SolarModule, NetworkModule
)
from hardware.sensor import SensorArray


class HardwareFactory:
    """
    Factory class responsible for building complete hardware configurations.
    Each method returns a fully assembled hardware stack along with sensors.
    """

    @staticmethod
    def create_food_kiosk_hardware(kiosk_id: str):
        """
        Food kiosks require refrigeration, solar support, and network connectivity.
        """
        base_hw = BaseDispenser(kiosk_id)
        fridge_hw = RefrigerationModule(base_hw, target_temp_c=4.0)
        solar_hw = SolarModule(fridge_hw)
        final_hw = NetworkModule(solar_hw, ssid="MetroNet")

        sensor_pack = SensorArray(kiosk_id)

        print(f"[HardwareFactory] Food kiosk hardware ready for {kiosk_id}")
        return final_hw, sensor_pack

    @staticmethod
    def create_pharmacy_kiosk_hardware(kiosk_id: str):
        """
        Pharmacy kiosks require refrigeration (for medicines) and network.
        """
        base_hw = BaseDispenser(kiosk_id)
        fridge_hw = RefrigerationModule(base_hw, target_temp_c=2.0)
        final_hw = NetworkModule(fridge_hw, ssid="HospitalNet")

        sensor_pack = SensorArray(kiosk_id)

        print(f"[HardwareFactory] Pharmacy kiosk hardware ready for {kiosk_id}")
        return final_hw, sensor_pack

    @staticmethod
    def create_emergency_kiosk_hardware(kiosk_id: str):
        """
        Emergency kiosks require solar power and network connectivity.
        No refrigeration is needed for non-perishable supplies.
        """
        base_hw = BaseDispenser(kiosk_id)
        solar_hw = SolarModule(base_hw)
        final_hw = NetworkModule(solar_hw, ssid="EmergencyNet")

        sensor_pack = SensorArray(kiosk_id)

        print(f"[HardwareFactory] Emergency kiosk hardware ready for {kiosk_id}")
        return final_hw, sensor_pack

    @staticmethod
    def create_basic_hardware(kiosk_id: str):
        """
        Basic setup with only core hardware and sensors.
        No additional modules attached.
        """
        base_hw = BaseDispenser(kiosk_id)
        sensor_pack = SensorArray(kiosk_id)

        print(f"[HardwareFactory] Basic hardware ready for {kiosk_id}")
        return base_hw, sensor_pack