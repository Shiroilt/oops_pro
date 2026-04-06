"""
File: core/kiosk.py
Purpose: Base Kiosk class — shared properties and behaviour for all kiosk types.
All specific kiosks (PharmacyKiosk, FoodKiosk, etc.) inherit from this.
"""

from core.central_registry import CentralRegistry


class Kiosk:
    """
    Base class for all kiosk types.
    Demonstrates: Encapsulation, Inheritance, Abstraction
    """

    def __init__(self, kiosk_id: str, location: str, kiosk_type: str):
        self.kiosk_id = kiosk_id
        self.location = location
        self.kiosk_type = kiosk_type
        self._mode = "ACTIVE"           # ACTIVE | MAINTENANCE | OFFLINE
        self._hardware = None
        self._payment_processor = None
        self._inventory = []
        self._registry = CentralRegistry()

        # Register this kiosk in the global registry
        self._registry.update_kiosk_status(kiosk_id, {
            "location": location,
            "type": kiosk_type,
            "mode": self._mode,
        })

    # ── Mode Management ───────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        allowed = ["ACTIVE", "MAINTENANCE", "OFFLINE"]
        if mode not in allowed:
            print(f"[Kiosk {self.kiosk_id}] Invalid mode '{mode}'")
            return
        self._mode = mode
        self._registry.update_kiosk_status(self.kiosk_id, {"mode": mode})
        print(f"[Kiosk {self.kiosk_id}] Mode changed to {mode}")

    def get_mode(self) -> str:
        return self._mode

    def is_operational(self) -> bool:
        return self._mode == "ACTIVE"

    # ── Hardware / Payment Setters ─────────────────────────────────────────────

    def set_hardware(self, hardware):
        self._hardware = hardware

    def set_payment_processor(self, processor):
        self._payment_processor = processor

    def set_inventory(self, inventory: list):
        self._inventory = inventory

    # ── Info ──────────────────────────────────────────────────────────────────

    def get_info(self) -> dict:
        return {
            "kiosk_id": self.kiosk_id,
            "location": self.location,
            "type": self.kiosk_type,
            "mode": self._mode,
        }

    def display_info(self):
        info = self.get_info()
        print(f"\n[Kiosk] ID: {info['kiosk_id']} | Type: {info['type']} "
              f"| Location: {info['location']} | Mode: {info['mode']}")

    def __str__(self):
        return f"Kiosk({self.kiosk_id}, {self.kiosk_type}, {self._mode})"
