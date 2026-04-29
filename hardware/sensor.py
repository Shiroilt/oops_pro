"""
File: hardware/sensor.py
Purpose: Kiosk sensor array — weight + IR sensors.
         Used by kiosk to verify dispensing success.
"""


class WeightSensor:
    def __init__(self, sensor_id: str):
        self.sensor_id   = sensor_id
        self._calibrated = True
        self._weight_g   = 0.0

    def read_weight(self) -> float:
        return self._weight_g

    def is_calibrated(self) -> bool:
        return self._calibrated

    def calibrate(self):
        self._calibrated = True
        print(f"  [Sensor {self.sensor_id}] Calibrated.")

    def get_status(self) -> dict:
        return {"id": self.sensor_id, "calibrated": self._calibrated,
                "weight_g": self._weight_g}


class IRSensor:
    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self._blocked  = False

    def is_slot_clear(self) -> bool:
        return not self._blocked

    def get_status(self) -> dict:
        return {"id": self.sensor_id, "slot_clear": not self._blocked}
