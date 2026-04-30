"""
DESIGN PATTERN: Observer (Behavioral)
File: city_monitor/monitor.py
Purpose: Implements a city-wide monitoring system using event-driven design.

         Instead of direct dependencies, subsystems communicate via events,
         ensuring loose coupling and scalability.

         Event Types:
           - LowStockEvent
           - HardwareFailureEvent
           - EmergencyModeActivatedEvent
           - TransactionFailedEvent
           - RestockEvent

         Subscribers:
           - MaintenanceService
           - SupplyChainSystem
           - CityMonitoringCenter

         EventBus acts as a Singleton mediator.
"""

from abc import ABC, abstractmethod
from datetime import datetime


# ── Event Definitions ─────────────────────────────────────────────────────────

class Event:
    """
    Base class for all events.
    Contains source identifier, message, and timestamp.
    """

    def __init__(self, kiosk_id: str, description: str):
        self.kiosk_id   = kiosk_id
        self.description = description
        self.timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"[{self.timestamp}] [{self.kiosk_id}] {self.description}"


class LowStockEvent(Event):
    def __init__(self, kiosk_id: str, product_name: str, remaining_qty: int):
        super().__init__(
            kiosk_id,
            f"LOW STOCK: '{product_name}' only {remaining_qty} units left"
        )
        self.product_name = product_name
        self.remaining_qty = remaining_qty


class HardwareFailureEvent(Event):
    def __init__(self, kiosk_id: str, failed_component: str):
        super().__init__(
            kiosk_id,
            f"HARDWARE FAILURE: {failed_component} malfunction detected"
        )
        self.failed_component = failed_component


class EmergencyModeActivatedEvent(Event):
    def __init__(self, kiosk_id: str):
        super().__init__(
            kiosk_id,
            "EMERGENCY MODE ACTIVATED — restrictions applied"
        )


class TransactionFailedEvent(Event):
    def __init__(self, kiosk_id: str, failure_reason: str):
        super().__init__(
            kiosk_id,
            f"TRANSACTION FAILED: {failure_reason}"
        )


class RestockEvent(Event):
    def __init__(self, kiosk_id: str, product_name: str, qty_added: int):
        super().__init__(
            kiosk_id,
            f"RESTOCKED: '{product_name}' +{qty_added} units"
        )


# ── Observer Interface ────────────────────────────────────────────────────────

class EventSubscriber(ABC):
    """
    Abstract observer interface.
    Any system interested in events must implement this.
    """

    @abstractmethod
    def on_event(self, event: Event):
        pass


# ── Concrete Subscribers ─────────────────────────────────────────────────────

class MaintenanceService(EventSubscriber):
    """Handles hardware failures by scheduling maintenance."""

    def on_event(self, event: Event):
        if isinstance(event, HardwareFailureEvent):
            print(f"  [Maintenance] Alert: {event}")
            print(f"  [Maintenance] Technician scheduled for {event.kiosk_id}")


class SupplyChainSystem(EventSubscriber):
    """Handles low stock events by triggering restock operations."""

    def on_event(self, event: Event):
        if isinstance(event, LowStockEvent):
            print(f"  [SupplyChain] Alert: {event}")
            print(f"  [SupplyChain] Ordering stock for '{event.product_name}'")


class CityMonitoringCenter(EventSubscriber):
    """Central logging system — records all events."""

    def __init__(self):
        from persistence.file_handler import FileHandler
        self._event_log = FileHandler.load_events()

    def on_event(self, event: Event):
        from persistence.file_handler import FileHandler
        log_entry = str(event)
        self._event_log.append(log_entry)
        FileHandler.save_event(log_entry)
        print(f"  [CityMonitor] {event}")

    def get_log(self) -> list:
        return list(self._event_log)

    def display_log(self):
        print("\n  [CityMonitor] === EVENT LOG ===")
        if not self._event_log:
            print("  No events recorded.")
            return
        for entry in self._event_log:
            print(f"  {entry}")
        print(f"\n  Total events: {len(self._event_log)}")


# ── Event Bus (Singleton Publisher) ──────────────────────────────────────────

class EventBus:
    """
    Singleton Event Dispatcher.

    Responsible for:
    - Registering subscribers
    - Broadcasting events to all observers

    Ensures decoupling between event producers and consumers.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Default subscribers
            cls._instance._subscribers = [
                MaintenanceService(),
                SupplyChainSystem(),
            ]

            cls._instance._city_monitor = CityMonitoringCenter()
            cls._instance._subscribers.append(cls._instance._city_monitor)

        return cls._instance

    def subscribe(self, subscriber: EventSubscriber):
        """Register a new subscriber."""
        self._subscribers.append(subscriber)

    def publish(self, event: Event):
        """Notify all subscribers of an event."""
        for subscriber in self._subscribers:
            subscriber.on_event(event)

    def get_city_monitor(self) -> CityMonitoringCenter:
        return self._city_monitor