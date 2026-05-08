"""
File: hardware/sensor.py
Purpose: Defines kiosk sensor modules (Weight + IR sensors).

         Sensors are used to validate successful product dispensing
         and monitor hardware health status.
"""


class WeightSensor:
    """
    Simulates a weight sensor attached to the kiosk.
    Used for detecting item presence and verifying dispensing.
    """

    def __init__(self, sensor_id: str):
        self.sensor_id      = sensor_id
        self._is_calibrated = True
        self._current_weight_g = 0.0

    def read_weight(self) -> float:
        return self._current_weight_g

    def is_calibrated(self) -> bool:
        return self._is_calibrated

    def calibrate(self):
        self._is_calibrated = True
        print(f"  [Sensor {self.sensor_id}] Calibrated.")

    def get_status(self) -> dict:
        return {
            "id":          self.sensor_id,
            "calibrated":  self._is_calibrated,
            "weight_g":    self._current_weight_g
        }


class IRSensor:
    """
    Infrared slot sensor.
    Detects whether dispensing slot is blocked or clear.
    """

    def __init__(self, sensor_id: str):
        self.sensor_id   = sensor_id
        self._slot_blocked = False

    def is_slot_clear(self) -> bool:
        return not self._slot_blocked

    def get_status(self) -> dict:
        return {
            "id": self.sensor_id,
            "slot_clear": not self._slot_blocked
        }


class SensorArray:
    """
    Aggregates all kiosk sensors into one interface.
    Used for diagnostics and dispense verification.
    """

    def __init__(self, kiosk_id: str):
        self.kiosk_id      = kiosk_id
        self.weight_sensor = WeightSensor(f"{kiosk_id}-WS")
        self.ir_sensor     = IRSensor(f"{kiosk_id}-IR")

    def all_ok(self) -> bool:
        """
        Returns True if all sensors report healthy status.
        """
        return (
            self.weight_sensor.is_calibrated() and
            self.ir_sensor.is_slot_clear()
        )

    def run_diagnostics(self) -> dict:
        """
        Collect diagnostics from all sensors.
        """
        return {
            "weight_sensor": self.weight_sensor.get_status(),
            "ir_sensor":     self.ir_sensor.get_status(),
        }

    def display(self):
        """
        Display current sensor health information.
        """
        overall = "OK" if self.all_ok() else "FAULT"

        print(
            f"  [Sensors] "
            f"Weight: {'OK' if self.weight_sensor.is_calibrated() else 'FAULT'} | "
            f"IR: {'CLEAR' if self.ir_sensor.is_slot_clear() else 'BLOCKED'} | "
            f"Overall: {overall}"
        )