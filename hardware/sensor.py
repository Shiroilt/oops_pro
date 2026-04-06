"""
File: hardware/sensor.py
Purpose: Simulates kiosk sensors — weight sensor, IR sensor, temperature probe.
         Used by the kiosk to detect hardware faults and monitor the environment.
"""


class WeightSensor:
    """Detects whether a product has been dispensed by monitoring tray weight."""

    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self._calibrated = True

    def read_weight_grams(self) -> float:
        """Returns current tray weight in grams (simulated)."""
        return 0.0      # 0 means tray is empty / item was dispensed

    def is_calibrated(self) -> bool:
        return self._calibrated

    def calibrate(self):
        self._calibrated = True
        print(f"  [WeightSensor {self.sensor_id}] Calibration complete.")

    def get_status(self) -> dict:
        return {
            "sensor_id": self.sensor_id,
            "type": "weight",
            "calibrated": self._calibrated,
            "reading_g": self.read_weight_grams(),
        }


class IRSensor:
    """Infrared sensor — detects presence of user or item in dispensing slot."""

    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self._blocked = False

    def is_slot_blocked(self) -> bool:
        """Returns True if something is blocking the dispensing slot."""
        return self._blocked

    def get_status(self) -> dict:
        return {
            "sensor_id": self.sensor_id,
            "type": "IR",
            "slot_blocked": self._blocked,
        }


class SensorArray:
    """
    Groups all sensors for a kiosk.
    Provides a single diagnostics interface over all sensors.
    """

    def __init__(self, kiosk_id: str):
        self.kiosk_id = kiosk_id
        self.weight_sensor = WeightSensor(f"{kiosk_id}-WS")
        self.ir_sensor = IRSensor(f"{kiosk_id}-IR")

    def run_diagnostics(self) -> dict:
        return {
            "weight_sensor": self.weight_sensor.get_status(),
            "ir_sensor": self.ir_sensor.get_status(),
        }

    def all_ok(self) -> bool:
        return (self.weight_sensor.is_calibrated() and
                not self.ir_sensor.is_slot_blocked())

    def display_status(self):
        print(f"  [SensorArray {self.kiosk_id}]")
        print(f"    Weight sensor : {'OK' if self.weight_sensor.is_calibrated() else 'FAULT'}")
        print(f"    IR sensor     : {'CLEAR' if not self.ir_sensor.is_slot_blocked() else 'BLOCKED'}")
