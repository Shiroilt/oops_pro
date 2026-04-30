"""
DESIGN PATTERN: State Pattern
File: core/kiosk.py
Purpose: Base Kiosk class.
         Kiosk mode follows State pattern: ACTIVE → MAINTENANCE → OFFLINE.
         Operational status is derived from mode + hardware health.
         Emergency mode enforces per-user purchase limits.
"""

from core.central_registry import CentralRegistry
from city_monitor.monitor import EventBus, EmergencyModeActivatedEvent
from pricing.pricing_strategy import PricingContext, EmergencyPricing, StandardPricing

EMERGENCY_STOCK_THRESHOLD = 5
EMERGENCY_PURCHASE_LIMIT  = 2


# ── State Interface ────────────────────────────────────────────────────────────

class KioskState:
    """Abstract State — each mode defines its own behaviour."""

    def get_mode_name(self) -> str:
        raise NotImplementedError

    def can_sell(self) -> bool:
        raise NotImplementedError

    def can_restock(self) -> bool:
        raise NotImplementedError


class ActiveState(KioskState):
    def get_mode_name(self): return "ACTIVE"
    def can_sell(self):     return True
    def can_restock(self):  return True


class MaintenanceState(KioskState):
    def get_mode_name(self): return "MAINTENANCE"
    def can_sell(self):     return False
    def can_restock(self):  return True


class OfflineState(KioskState):
    def get_mode_name(self): return "OFFLINE"
    def can_sell(self):     return False
    def can_restock(self):  return False


_STATE_MAP = {
    "ACTIVE":      ActiveState(),
    "MAINTENANCE": MaintenanceState(),
    "OFFLINE":     OfflineState(),
}


# ── Base Kiosk ────────────────────────────────────────────────────────────────

class Kiosk:
    """
    Base class for all kiosk types.
    STATE PATTERN: mode transitions control sell/restock permissions.
    """

    def __init__(self, kiosk_id: str, location: str, kiosk_type: str, password: str = "1234"):
        self.kiosk_id   = kiosk_id
        self.location   = location
        self.kiosk_type = kiosk_type
        self.password   = password
        self._state: KioskState = ActiveState()
        self._hardware          = None
        self._sensors           = None
        self._payment_processor = None
        self._inventory         = None
        self._pricing           = PricingContext(StandardPricing())
        self._emergency_mode    = False
        self._user_purchase_counts: dict = {}
        self._registry = CentralRegistry()
        self._registry.update_kiosk_status(kiosk_id, {
            "location":  location,
            "type":      kiosk_type,
            "mode":      self._state.get_mode_name(),
        })

    # ── State Transitions ─────────────────────────────────────────────────────

    def set_mode(self, mode: str):
        state = _STATE_MAP.get(mode)
        if not state:
            print(f"  [Kiosk] Unknown mode: {mode}")
            return
        self._state = state
        self._registry.update_kiosk_status(self.kiosk_id, {"mode": mode})
        print(f"  [Kiosk {self.kiosk_id}] State → {mode}")

    def get_mode(self) -> str:
        return self._state.get_mode_name()

    # ── Operational Check ─────────────────────────────────────────────────────

    def is_operational(self) -> bool:
        """
        Kiosk is operational only if:
        - state allows selling
        - hardware is healthy
        """
        if not self._state.can_sell():
            return False
        if self._hardware and not self._hardware.is_healthy():
            return False
        return True

    # ── Emergency Mode ────────────────────────────────────────────────────────

    def check_and_activate_emergency(self):
        """Auto-activate emergency mode if any item stock is critically low."""
        if self._inventory and not self._emergency_mode:
            low_items = self._inventory.get_low_stock_items(EMERGENCY_STOCK_THRESHOLD)
            if low_items:
                self._activate_emergency_mode()

    def _activate_emergency_mode(self):
        self._emergency_mode = True
        self._pricing.set_strategy(EmergencyPricing())
        EventBus().publish(EmergencyModeActivatedEvent(self.kiosk_id))
        print(f"\n  *** EMERGENCY MODE ACTIVATED on {self.kiosk_id} ***")
        print(f"  *** Each user limited to {EMERGENCY_PURCHASE_LIMIT} items ***")
        print(f"  *** All items are now FREE ***\n")

    def deactivate_emergency_mode(self):
        self._emergency_mode = False
        self._pricing.set_strategy(StandardPricing())
        print(f"  [Kiosk] Emergency mode deactivated on {self.kiosk_id}")

    # ── Purchase Limits ───────────────────────────────────────────────────────

    def can_user_purchase(self, user_id: str) -> bool:
        if self._emergency_mode:
            count = self._user_purchase_counts.get(user_id, 0)
            return count < EMERGENCY_PURCHASE_LIMIT
        return True

    def record_purchase(self, user_id: str):
        self._user_purchase_counts[user_id] = (
            self._user_purchase_counts.get(user_id, 0) + 1
        )

    def get_purchase_count(self, user_id: str) -> int:
        return self._user_purchase_counts.get(user_id, 0)

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_hardware(self, hardware):
        self._hardware = hardware
        if self._inventory and hardware:
            self._inventory.enforce_hardware_constraints(
                hardware.get_capabilities()
            )

    def set_sensors(self, sensors):
        self._sensors = sensors

    def set_payment_processor(self, processor):
        self._payment_processor = processor

    def set_inventory(self, inventory):
        self._inventory = inventory
        if self._hardware and inventory:
            self._inventory.enforce_hardware_constraints(
                self._hardware.get_capabilities()
            )

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Produces a robust dictionary representation of the entire Kiosk state
        suitable for serialization to persistent JSON storage.
        """
        # Step 1: Serialize the active payment processor (if any)
        serialized_payment_processor = dict()
        has_processor = self._payment_processor is not None
        can_serialize_processor = hasattr(self._payment_processor, 'to_dict')
        
        if has_processor and can_serialize_processor:
            serialized_payment_processor = self._payment_processor.to_dict()

        # Step 2: Extract active hardware capabilities
        active_hardware_capabilities = list()
        if self._hardware is not None:
            active_hardware_capabilities = self._hardware.get_capabilities()

        # Step 3: Snapshot the current inventory state
        snapshot_inventory = list()
        if self._inventory is not None:
            snapshot_inventory = self._inventory.to_list()

        # Step 4: Construct the final state payload mapping
        state_payload = dict()
        state_payload["kiosk_id"] = self.kiosk_id
        state_payload["location"] = self.location
        state_payload["kiosk_type"] = self.kiosk_type
        state_payload["password"] = self.password
        state_payload["mode"] = self._state.get_mode_name()
        state_payload["payment"] = serialized_payment_processor
        state_payload["hardware_modules"] = active_hardware_capabilities
        state_payload["inventory"] = snapshot_inventory

        return state_payload

    # ── Display ───────────────────────────────────────────────────────────────

    def display_info(self):
        status    = "OPERATIONAL" if self.is_operational() else "NOT OPERATIONAL"
        emergency = " [EMERGENCY MODE]" if self._emergency_mode else ""
        print(f"\n  Kiosk     : {self.kiosk_id}")
        print(f"  Type      : {self.kiosk_type}")
        print(f"  Location  : {self.location}")
        print(f"  State     : {self._state.get_mode_name()}{emergency}")
        print(f"  Status    : {status}")
        if self._hardware:
            print(f"  Hardware  : {self._hardware.get_status()}")
        if self._payment_processor:
            print(f"  Payment   : {self._payment_processor.get_provider_name()}")
        else:
            print(f"  Payment   : Selected by user at purchase time")
        if self._pricing:
            print(f"  Pricing   : {self._pricing.get_strategy_name()}")
