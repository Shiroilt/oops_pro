"""
DESIGN PATTERN: Observer (Behavioral)
File: city_monitor/monitor.py
Purpose: City Monitoring System — subsystems communicate through events
         instead of direct dependencies (loose coupling).

Events published:
  LowStockEvent            — item stock below threshold
  HardwareFailureEvent     — hardware component failed
  EmergencyModeActivatedEvent — kiosk entered emergency mode
  TransactionFailedEvent   — a purchase or refund failed
  RestockEvent             — admin restocked an item

Subscribers:
  MaintenanceService       — responds to hardware failures
  SupplyChainSystem        — responds to low stock
  CityMonitoringCenter     — logs ALL events (central dashboard)

EventBus is a Singleton publisher/broker.
"""

from abc import ABC, abstractmethod
from datetime import datetime


# ── Events ────────────────────────────────────────────────────────────────────

class Event:
    """Base event — all events carry source kiosk, message, and timestamp."""

    def __init__(self, source_kiosk: str, message: str):
        self.source_kiosk = source_kiosk
        self.message      = message
        self.timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"[{self.timestamp}] [{self.source_kiosk}] {self.message}"


class LowStockEvent(Event):
    def __init__(self, kiosk_id: str, item_name: str, remaining: int):
        super().__init__(kiosk_id,
                         f"LOW STOCK: '{item_name}' has only {remaining} units left")
        self.item_name = item_name
        self.remaining = remaining


class HardwareFailureEvent(Event):
    def __init__(self, kiosk_id: str, component: str):
        super().__init__(kiosk_id, f"HARDWARE FAILURE: {component} has failed")
        self.component = component


class EmergencyModeActivatedEvent(Event):
    def __init__(self, kiosk_id: str):
        super().__init__(kiosk_id,
                         "EMERGENCY MODE ACTIVATED — purchase limits enforced")


class TransactionFailedEvent(Event):
    def __init__(self, kiosk_id: str, reason: str):
        super().__init__(kiosk_id, f"TRANSACTION FAILED: {reason}")


class RestockEvent(Event):
    def __init__(self, kiosk_id: str, item_name: str, quantity: int):
        super().__init__(kiosk_id,
                         f"RESTOCKED: '{item_name}' +{quantity} units")


# ── Observer Interface ────────────────────────────────────────────────────────

class EventSubscriber(ABC):
    """Abstract Observer — all monitoring services implement this."""

    @abstractmethod
    def on_event(self, event: Event):
        pass


# ── Concrete Subscribers (Observers) ─────────────────────────────────────────

class MaintenanceService(EventSubscriber):
    """Responds to hardware failure events — schedules technicians."""

    def on_event(self, event: Event):
        if isinstance(event, HardwareFailureEvent):
            print(f"  [MaintenanceService] Alert: {event}")
            print(f"  [MaintenanceService] Scheduling technician for "
                  f"{event.source_kiosk}")


class SupplyChainSystem(EventSubscriber):
    """Responds to low stock events — initiates restock orders."""

    def on_event(self, event: Event):
        if isinstance(event, LowStockEvent):
            print(f"  [SupplyChain] Alert: {event}")
            print(f"  [SupplyChain] Initiating restock order for "
                  f"'{event.item_name}'")


class CityMonitoringCenter(EventSubscriber):
    """Receives ALL events — central city dashboard and audit log."""

    def __init__(self):
        from persistence.file_handler import FileHandler
        self._log = FileHandler.load_events()

    def on_event(self, event: Event):
        from persistence.file_handler import FileHandler
        entry = str(event)
        self._log.append(entry)
        FileHandler.save_event(entry)
        print(f"  [CityMonitor] {event}")

    def get_log(self) -> list:
        return list(self._log)

    def display_log(self):
        print("\n  [CityMonitor] === EVENT LOG ===")
        if not self._log:
            print("  No events recorded yet.")
            return
        for entry in self._log:
            print(f"  {entry}")
        print(f"\n  Total events: {len(self._log)}")


# ── Event Bus (Singleton Publisher) ──────────────────────────────────────────

class EventBus:
    """
    OBSERVER PATTERN — Singleton Publisher/Broker.
    All subsystems use EventBus to fire and receive events.
    Decouples event producers from consumers entirely.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Register default city services as subscribers
            cls._instance._subscribers = [
                MaintenanceService(),
                SupplyChainSystem(),
            ]
            cls._instance._city_monitor = CityMonitoringCenter()
            cls._instance._subscribers.append(cls._instance._city_monitor)
        return cls._instance

    def subscribe(self, subscriber: EventSubscriber):
        """Add a new subscriber to receive all future events."""
        self._subscribers.append(subscriber)

    def publish(self, event: Event):
        """Fire an event — delivered to ALL subscribers."""
        for subscriber in self._subscribers:
            subscriber.on_event(event)

    def get_city_monitor(self) -> CityMonitoringCenter:
        return self._city_monitor
