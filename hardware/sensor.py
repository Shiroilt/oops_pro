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
class SensorArray:
    """Groups all sensors for a kiosk. Used to verify successful dispensing."""

    def __init__(self, kiosk_id: str):
        self.kiosk_id = kiosk_id
        self.weight   = WeightSensor(f"{kiosk_id}-WS")
        self.ir       = IRSensor(f"{kiosk_id}-IR")

    def all_ok(self) -> bool:
        return self.weight.is_calibrated() and self.ir.is_slot_clear()

    def run_diagnostics(self) -> dict:
        return {
            "weight_sensor": self.weight.get_status(),
            "ir_sensor":     self.ir.get_status(),
        }

    def display(self):
        ok = "OK" if self.all_ok() else "FAULT"
        print(f"  [Sensors] Weight: {'OK' if self.weight.is_calibrated() else 'FAULT'} | "
              f"IR: {'CLEAR' if self.ir.is_slot_clear() else 'BLOCKED'} | Overall: {ok}")
