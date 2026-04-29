# AURA Retail OS — Smart City Modular Kiosk Platform

> **A Python-based vending machine simulation demonstrating 10+ Gang-of-Four design patterns in a real-world smart city context.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Design Patterns](https://img.shields.io/badge/Design%20Patterns-10%2B-purple)](docs/)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture & Code Explanation](#architecture--code-explanation)
  - [Module Structure](#module-structure)
  - [core — Kiosk Base & Facade](#core--kiosk-base--facade)
  - [kiosk — Specialized Kiosk Types](#kiosk--specialized-kiosk-types)
  - [product — Inventory & Composite](#product--inventory--composite)
  - [payment — Adapter & Strategy](#payment--adapter--strategy)
  - [hardware — Decorator Chain](#hardware--decorator-chain)
  - [commands — Command Pattern](#commands--command-pattern)
  - [pricing — Strategy Pattern](#pricing--strategy-pattern)
  - [city_monitor — Observer / Event Bus](#city_monitor--observer--event-bus)
  - [persistence — File-Based Storage](#persistence--file-based-storage)
  - [main.py — Entry Point & CLI](#mainpy--entry-point--cli)
- [Design Patterns Reference](#design-patterns-reference)
- [How to Clone & Run](#how-to-clone--run)
- [Simulation Demonstration & Steps](#simulation-demonstration--steps)
  - [Admin Simulation: Creating a Kiosk](#admin-simulation-creating-a-kiosk)
  - [User Simulation: Buying an Item](#user-simulation-buying-an-item)
  - [Emergency Mode Simulation](#emergency-mode-simulation)
  - [Refund Simulation](#refund-simulation)
  - [City Monitor Event Log](#city-monitor-event-log)
- [Data Persistence](#data-persistence)
- [Running Tests](#running-tests)

---

## Project Overview

**AURA Retail OS** is a terminal-based smart city vending machine platform. It models a city-wide network of intelligent kiosks — food, pharmacy, and emergency — each independently configurable with modular hardware, dynamic pricing, flexible payment methods, and a real-time city event monitoring system.

The project is primarily an **academic design patterns showcase**, with every major subsystem mapping to one or more classic Gang-of-Four patterns.

### Key Features

- Three kiosk types: **Food**, **Pharmacy**, **Emergency**
- Modular hardware stacks: Refrigeration, Solar Power, Network
- Three payment methods selectable at purchase time: UPI, Card, Wallet
- Dynamic pricing: Standard, Discounted, Emergency (Free), Surge
- Full transaction lifecycle: purchase, refund, restock, audit log
- Automatic emergency mode when stock falls critically low
- Per-user purchase limits under emergency conditions
- City-wide event monitoring dashboard
- All state persisted to `persistence/data.json` across sessions

---

## Architecture & Code Explanation

### Module Structure

```
vending_machine/
├── main.py                    # Entry point — CLI, admin/user menus
├── core/
│   ├── kiosk.py               # Base Kiosk class (State Pattern)
│   ├── kiosk_interface.py     # Facade — single public API
│   └── central_registry.py    # Singleton — global status registry
├── kiosk/
│   ├── kiosk_factory.py       # Factory Method — builds typed kiosks
│   ├── food_kiosk.py          # FoodKiosk subclass
│   ├── pharmacy_kiosk.py      # PharmacyKiosk subclass
│   └── emergency_kiosk.py     # EmergencyKiosk subclass
├── product/
│   ├── product.py             # Composite Leaf — single product
│   ├── bundle.py              # Composite Branch — product bundle
│   ├── inventory.py           # Inventory manager
│   ├── product_factory.py     # Abstract Factory — product families
│   └── inventory_proxy.py     # Proxy — role-based access control
├── payment/
│   ├── payment_interface.py   # Abstract Target interface
│   ├── adapter.py             # Adapter — UPI / Card / Wallet
│   └── payment_selector.py    # Strategy selector at purchase time
├── hardware/
│   ├── dispenser.py           # Decorator chain — hardware modules
│   ├── dispenser_types.py     # Concrete dispenser variants
│   ├── hardware_factory.py    # Factory — assembles hardware stacks
│   └── sensor.py              # Weight + IR sensor array
├── commands/
│   ├── command.py             # Abstract Command + CommandHistory
│   ├── purchase_command.py    # Atomic purchase with rollback
│   ├── refund_command.py      # Atomic refund with rollback
│   └── restock_command.py     # Admin restock command
├── pricing/
│   └── pricing_strategy.py    # Strategy — 4 pricing modes
├── city_monitor/
│   └── monitor.py             # Observer — EventBus + subscribers
└── persistence/
    ├── file_handler.py        # JSON persistence layer
    └── data.json              # Live system state (auto-generated)
```

---

### core — Kiosk Base & Facade

#### `core/kiosk.py` — State Pattern

The `Kiosk` base class is the heart of the system. It implements the **State Pattern** to model the kiosk's operational lifecycle.

```
ACTIVE ──────────────── can sell, can restock
MAINTENANCE ─────────── cannot sell, can restock
OFFLINE ─────────────── cannot sell, cannot restock
```

Three state classes (`ActiveState`, `MaintenanceState`, `OfflineState`) each implement the `KioskState` interface with `can_sell()` and `can_restock()` methods. The kiosk delegates these decisions to its current state object — no if/else chains needed.

**Emergency Mode** is an overlay on top of the state machine. When any item's stock drops to or below `EMERGENCY_STOCK_THRESHOLD = 5`, the kiosk auto-activates emergency mode: pricing switches to `EmergencyPricing` (everything free), and each user is limited to `EMERGENCY_PURCHASE_LIMIT = 2` items.

```python
# State transition example
kiosk.set_mode("MAINTENANCE")   # ACTIVE → MAINTENANCE
kiosk.is_operational()          # False — state.can_sell() is False
```

#### `core/kiosk_interface.py` — Facade Pattern

`KioskInterface` is the **only** public API for all kiosk operations. External code (main menus, tests) never touches inventory, payment, hardware, or commands directly — everything is routed through this facade.

Internally, every operation is wrapped in a Command object:
- `purchase_item()` → creates and executes a `PurchaseCommand`
- `refund_transaction()` → creates and executes a `RefundCommand`
- `restock_inventory()` → creates and executes a `RestockCommand`
- `run_diagnostics()` → delegates to hardware stack
- `show_inventory()` / `show_kiosk_info()` → display helpers

The facade also handles state persistence — every successful operation calls `_save_kiosk_state()` to write updated kiosk data to `data.json`.

#### `core/central_registry.py` — Singleton Pattern

`CentralRegistry` is a **Singleton** — only one instance ever exists system-wide (enforced via `__new__`). It loads saved configuration from `data.json` at startup and maintains a live in-memory map of all kiosk statuses. The registry also provides system-wide transaction summaries used by the admin dashboard.

---

### kiosk — Specialized Kiosk Types

Each kiosk type extends the base `Kiosk` with type-specific defaults:

| Type | Default Hardware | Products | Notes |
|------|-----------------|----------|-------|
| `FoodKiosk` | Fridge + Solar + Network | Food items | Regular pricing |
| `PharmacyKiosk` | Fridge (2°C) + Network | Medical items | Regular pricing |
| `EmergencyKiosk` | Solar + Network | Relief supplies | Always FREE |

#### `kiosk/kiosk_factory.py` — Factory Method Pattern

`KioskFactory` provides a **Factory Method** for each kiosk type. Each `create_*()` method assembles the correct kiosk subclass, hardware stack, and default inventory in one call. The `restore_from_dict()` method rebuilds any kiosk from its saved JSON representation, enabling cross-session persistence.

---

### product — Inventory & Composite

#### `product/product.py` and `product/bundle.py` — Composite Pattern

The product hierarchy uses the **Composite Pattern**:

- **`Product`** (Leaf) — a single sellable item. Manages its own stock, reservations, and hardware dependency (chilled items become unavailable without a refrigeration module).
- **`ProductBundle`** (Branch) — contains `Product` objects or nested `ProductBundle` objects. Price is the sum of children minus discount. Available stock is the minimum across all children (the bottleneck). Purchasing a bundle atomically deducts all contained items.

Both classes implement the same interface (`get_name()`, `get_price()`, `get_available_stock()`, `reserve()`, `confirm_sale()`), so calling code treats them identically.

```
Inventory
├── Product: "Water Bottle"   Rs.20   Stock:50
├── Product: "Sandwich"       Rs.60   Stock:20   [CHILLED]
└── Bundle:  "Meal Combo"     Rs.76.5 (10% off)
    ├── Product: "Sandwich"
    └── Product: "Chips"
```

#### `product/product_factory.py` — Abstract Factory Pattern

`ProductFactory.create_product(kiosk_type, ...)` is an **Abstract Factory** that returns the correct product subclass for a given kiosk family:

- `FoodKiosk` → `FoodProduct` (regular pricing, can be chilled)
- `PharmacyKiosk` → `PharmacyProduct` (regular pricing, medical display)
- `EmergencyKiosk` → `EmergencyProduct` (always priced at Rs.0)

Client code never references concrete product classes.

#### `product/inventory_proxy.py` — Proxy Pattern

`SecureInventoryProxy` wraps `Inventory` and enforces **role-based access control**. Only users with the `admin` role can call `restock()`. All access attempts are logged with timestamp, role, and outcome for auditing.

---

### payment — Adapter & Strategy

#### `payment/payment_interface.py`

`PaymentProcessor` is an abstract interface (Target) that defines three methods: `process_payment()`, `refund_payment()`, and `get_provider_name()`. The kiosk depends only on this interface.

#### `payment/adapter.py` — Adapter Pattern

Three incompatible third-party APIs are adapted into the `PaymentProcessor` interface:

| Adaptee (Raw API) | Adapter | Key translation |
|-------------------|---------|-----------------|
| `UPISystemAPI` | `UPIAdapter` | `initiate_upi_payment()` → `process_payment()` |
| `CardGatewayAPI` | `CardAdapter` | `charge_card()` (paise) → `process_payment()` (Rs.) |
| `DigitalWalletAPI` | `DigitalWalletAdapter` | `debit_wallet()` → `process_payment()` |

The kiosk never knows which underlying API it is using — it calls `process_payment()` and the adapter handles translation.

#### `payment/payment_selector.py` — Strategy Pattern (Behavioral)

`PaymentSelector.select_payment()` presents a menu at purchase time and returns the chosen `PaymentProcessor` as a **Strategy**. The selected adapter is injected into the kiosk for that transaction only. This means payment method is chosen per-purchase, not at kiosk creation — making each adapter a runtime-swappable strategy.

---

### hardware — Decorator Chain

#### `hardware/dispenser.py` — Decorator Pattern

The hardware system uses the **Decorator Pattern** to compose capabilities dynamically at runtime:

```
BaseDispenser                              # core motor + dispenser
  └── RefrigerationModule(base)            # + refrigeration
       └── SolarModule(fridge)             # + solar power
            └── NetworkModule(solar)       # + network connectivity
```

`BaseDispenser` is the concrete component. `HardwareDecorator` is the abstract decorator base. `RefrigerationModule`, `SolarModule`, and `NetworkModule` are concrete decorators — each wraps any `KioskHardware` and adds its capability to `get_capabilities()`.

Hardware health (`is_healthy()`) propagates through the chain: if any module reports a fault, the whole stack is unhealthy, and the kiosk becomes non-operational.

```python
hw = BaseDispenser("KIOSK-01")
hw = RefrigerationModule(hw, target_temp_c=4.0)
hw = SolarModule(hw)
hw.get_capabilities()
# → ["dispenser", "motor", "basic_power", "refrigeration", "solar_power"]
```

#### `hardware/dispenser_types.py`

Three concrete dispenser variants extend `BaseDispenser`:
- `SpiralDispenser` — adds `"spiral_mechanism"` capability
- `RoboticArmDispenser` — adds `"robotic_arm"` capability
- `ConveyorDispenser` — adds `"conveyor_belt"` capability

#### `hardware/hardware_factory.py` — Factory Pattern

`HardwareFactory` assembles pre-wired hardware decorator chains per kiosk type. `create_custom_hardware()` builds a chain from an admin-specified list of module names.

#### `hardware/sensor.py`

`SensorArray` groups a `WeightSensor` and `IRSensor` for each kiosk. Used during diagnostics to verify physical dispensing health.

---

### commands — Command Pattern

#### `commands/command.py`

`Command` is an abstract base class. Every operation implements `execute()` (returns `bool`) and `undo()` (rollback). Each command records its status (`PENDING`, `SUCCESS`, `FAILED`, `UNDONE`) and a log message.

`CommandHistory` is a **Singleton** that records every executed command in memory — a full in-session audit trail.

#### `commands/purchase_command.py`

`PurchaseCommand` executes a purchase in 8 atomic steps:

1. Check hardware dependency (chilled items need refrigeration module)
2. Check item stock availability
3. **Reserve stock** (atomic start — no double-sell)
4. Compute dynamic price via `PricingContext`
5. Process payment via `PaymentProcessor`
6. **Confirm sale** (reduce actual stock)
7. Check remaining stock → fire `LowStockEvent` if below threshold
8. Persist transaction to `data.json`

If step 5 (payment) fails → `undo()` releases the reservation. The purchase is fully rolled back automatically.

#### `commands/refund_command.py`

`RefundCommand` validates that the transaction belongs to the requesting user, calls `refund_payment()` on the payment processor, restores inventory stock, marks the original transaction as `REFUNDED` in the file, and logs a new `REFUND` transaction record.

#### `commands/restock_command.py`

`RestockCommand` saves the current stock level (for undo), adds the requested quantity, fires a `RestockEvent` to the city monitor, and persists the updated inventory. If restocking brings all items back above the emergency threshold, the kiosk's emergency mode is automatically deactivated.

---

### pricing — Strategy Pattern

#### `pricing/pricing_strategy.py`

Four concrete pricing strategies all implement the `PricingStrategy` interface:

| Strategy | Behaviour | When Used |
|---|---|---|
| `StandardPricing` | Returns base price | Default for all kiosks |
| `DiscountedPricing` | Applies % discount | Promotions |
| `EmergencyPricing` | Returns 0.0 (FREE) | Auto-activated in emergency mode |
| `SurgePricing` | Multiplies by surge factor | Peak demand |

`PricingContext` holds the active strategy and can swap it at runtime with `set_strategy()`. The kiosk calls `pricing_context.get_price(base_price)` — it never knows which strategy is active.

```python
pricing = PricingContext(StandardPricing())
pricing.get_price(60.0)   # → 60.0

pricing.set_strategy(EmergencyPricing())
pricing.get_price(60.0)   # → 0.0
```

---

### city_monitor — Observer / Event Bus

#### `city_monitor/monitor.py` — Observer Pattern

The city monitoring system implements the **Observer Pattern** with a Singleton `EventBus` as the publisher/broker.

**Events fired by the system:**

| Event | Fired When |
|---|---|
| `LowStockEvent` | Item stock falls ≤ 5 after a purchase |
| `HardwareFailureEvent` | Hardware component reports fault |
| `EmergencyModeActivatedEvent` | Kiosk enters emergency mode |
| `TransactionFailedEvent` | Purchase or refund fails |
| `RestockEvent` | Admin restocks an item |

**Subscribers (Observers):**

| Subscriber | Responds To |
|---|---|
| `MaintenanceService` | `HardwareFailureEvent` — logs technician alert |
| `SupplyChainSystem` | `LowStockEvent` — initiates restock order |
| `CityMonitoringCenter` | ALL events — central log and dashboard |

```python
# Firing an event — publisher and subscriber are decoupled
EventBus().publish(LowStockEvent("KIOSK-01", "Water Bottle", 3))
# → All subscribers receive the event automatically
```

`CityMonitoringCenter` persists all events to `data.json` and provides `display_log()` for the admin dashboard.

---

### persistence — File-Based Storage

#### `persistence/file_handler.py`

`FileHandler` is a static utility class that manages all reads and writes to `persistence/data.json`. The file has four top-level keys:

```json
{
  "kiosks":       { "KIOSK-01": { ... kiosk config, inventory ... } },
  "transactions": [ { "txn_id": "...", "type": "PURCHASE", ... } ],
  "events":       [ "[timestamp] [KIOSK-01] LOW STOCK: ..." ],
  "config":       {}
}
```

Every operation is atomic: load → modify → save. The file is auto-created on first run and survives process restarts — kiosks are fully restored from it at startup via `KioskFactory.restore_from_dict()`.

---

### main.py — Entry Point & CLI

`main.py` provides the full interactive CLI. At startup, the user selects a role:

- **Admin** (password: `root`) — full system management: create kiosks, add/restock items, manage hardware, change kiosk models, view city monitor events
- **User** — vending machine operations: view inventory, buy items/combos, refund, view personal transaction history

Payment method is **not** selected at kiosk creation. It is selected by the user at the moment of purchase, implementing a clean separation between kiosk setup and transaction processing.

---

## Design Patterns Reference

| Pattern | Category | File(s) | Usage |
|---|---|---|---|
| **Singleton** | Creational | `central_registry.py`, `command.py`, `monitor.py` | One global registry, one command history, one event bus |
| **Factory Method** | Creational | `kiosk/kiosk_factory.py` | Builds fully-wired kiosks by type |
| **Abstract Factory** | Creational | `product/product_factory.py` | Creates products per kiosk family |
| **Decorator** | Structural | `hardware/dispenser.py` | Composable hardware modules at runtime |
| **Facade** | Structural | `core/kiosk_interface.py` | Single API hiding all subsystems |
| **Proxy** | Structural | `product/inventory_proxy.py` | Role-based inventory access control |
| **Composite** | Structural | `product/product.py`, `product/bundle.py` | Products and bundles as uniform tree |
| **Adapter** | Structural | `payment/adapter.py` | UPI/Card/Wallet APIs → PaymentProcessor |
| **Command** | Behavioral | `commands/` | Atomic operations with undo/rollback |
| **Strategy** | Behavioral | `pricing/pricing_strategy.py`, `payment/payment_selector.py` | Swappable pricing and payment methods |
| **State** | Behavioral | `core/kiosk.py` | ACTIVE / MAINTENANCE / OFFLINE modes |
| **Observer** | Behavioral | `city_monitor/monitor.py` | Decoupled city-wide event system |

---

## How to Clone & Run

### Prerequisites

- Python **3.10 or higher**
- No third-party packages required — the entire project uses Python's standard library only

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/aura-retail-os.git
cd aura-retail-os
```

### Step 2 — Verify Python Version

```bash
python3 --version
# Should print Python 3.10.x or higher
```

### Step 3 — Run the Application

```bash
cd vending_machine
python3 main.py
```

> **Note:** Run from inside the `vending_machine/` directory so all relative imports and the `persistence/data.json` path resolve correctly.

### Step 4 — First-Time Setup

On first run, `persistence/data.json` does not exist. You will need to log in as Admin and create at least one kiosk before any user flow is available.

```
============================================================
   AURA RETAIL OS
   Smart City Modular Kiosk Platform
============================================================

  Who are you?
    1. User   — Browse & purchase from vending machines
    2. Admin  — Full system management (password required)
------------------------------------------------------------
  Select (1/2): 2
  Enter admin password: root
```

### Step 5 — Run Tests

```bash
cd vending_machine
python3 test_aura_system.py
```

Test output is also saved to `test_out.txt` for review.

### Optional: Reset All Data

To start fresh (wipe all saved kiosks and transactions):

```python
from persistence.file_handler import FileHandler
FileHandler.clear()
```

Or simply delete `persistence/data.json`.

---

## Simulation Demonstration & Steps

The following walkthroughs cover the complete user and admin journeys, including all major system behaviours. Run `python3 main.py` from inside `vending_machine/` to follow along interactively.

---

### Admin Simulation: Creating a Kiosk

**Goal:** Create a Food Kiosk with items, a combo, and hardware modules.

```
Select (1/2): 2
Enter admin password: root
Admin ID: admin_01

ADMIN MENU
  1. Create New Vending Machine
Select (0-9): 1

  Kiosk types:
    1. Food Kiosk       (Metro/Campus)
    2. Pharmacy Kiosk   (Hospital)
    3. Emergency Kiosk  (Disaster Zone)
Choose type (1/2/3): 1

  Kiosk ID:    KIOSK-01
  Location:    Central Metro
  Password:    1234

ADD ITEMS TO INVENTORY
  Item name: Water Bottle
  Price:     20
  Quantity:  50
  Refrigeration? n

  Item name: Cold Coffee
  Price:     60
  Quantity:  20
  Refrigeration? y        ← marks item as CHILLED

  Item name: done

ADD COMBO OPTIONS
  Add combos? y
  Combo name: Refresher Pack
  Discount %: 15
  Select items: 1, 2    ← Water Bottle + Cold Coffee
  Add another combo? n

SELECT HARDWARE MODULES
  Refrigeration? y        ← required for Cold Coffee to be available
  Solar power?   y
  Network?       y
  SSID: MetroNet

  Kiosk 'KIOSK-01' created and saved!
```

**What happened internally:**
- `FoodKiosk` was instantiated (via concrete subclass, not factory in this path)
- Hardware decorator chain was built: `BaseDispenser → RefrigerationModule → SolarModule → NetworkModule`
- `ProductFactory.create_product("FoodKiosk", ...)` created `FoodProduct` instances
- `ProductBundle` was assembled with a 15% discount
- `Inventory.enforce_hardware_constraints()` was called — Cold Coffee is now AVAILABLE because refrigeration is present
- `FileHandler.save_kiosk()` persisted everything to `data.json`

---

### User Simulation: Buying an Item

**Goal:** User buys 2 Water Bottles using UPI.

```
Select (1/2): 1
Enter User ID: user_01

VENDING MACHINE — Welcome, user_01
  1. Browse & Buy from Vending Machine

Select kiosk: 1   (KIOSK-01 — FoodKiosk @ Central Metro)

KIOSK: KIOSK-01 [FoodKiosk]
  2. Buy Item

BUY ITEM
  Current Inventory:
    [Food] Water Bottle      — Rs.20.00 | Stock: 50
    [Food] Cold Coffee [CHILLED] — Rs.60.00 | Stock: 20
    [Bundle] Refresher Pack  — Rs.68.00 (15% off) | Stock: 20

  Item name: Water Bottle
  Available: 50 | Price: Rs.20.00 each
  How many? (1-50): 2
  Order: 2x Water Bottle = Rs.40.00

  SELECT PAYMENT METHOD
    1. UPI
    2. Card
    3. Wallet
  Your choice: 1
  UPI VPA: user01@paytm

  Confirm purchase? y

[KioskInterface] Purchase: 2x 'Water Bottle' | User: user_01
  [UPI API] Paying Rs.20.00 to user01@paytm
  SUCCESS: Purchased 'Water Bottle' for Rs.20.00 via UPI (user01@paytm)
  [UPI API] Paying Rs.20.00 to user01@paytm
  SUCCESS: Purchased 'Water Bottle' for Rs.20.00 via UPI (user01@paytm)

  Purchase successful!
```

**What happened internally:**
- `KioskInterface.purchase_item()` was called
- `PaymentSelector.select_payment()` returned a `UPIAdapter` (Strategy)
- Two `PurchaseCommand` objects were created and executed sequentially
- Each command: reserved stock → computed price via `PricingContext` → called `UPIAdapter.process_payment()` → confirmed sale → checked low stock
- `CommandHistory` recorded both commands
- Updated kiosk state saved to `data.json`

---

### Emergency Mode Simulation

**Goal:** Watch the system auto-activate emergency mode as stock drops.

```
# Admin restocks Cold Coffee to only 5 units (at the threshold)
Admin: Restock → Cold Coffee → quantity: -15 (bring to 5)

# User purchases Cold Coffee
BUY ITEM → Cold Coffee

[KioskInterface] Purchase: 1x 'Cold Coffee' | User: user_02
  [CityMonitor] LOW STOCK: 'Cold Coffee' has only 4 units left
  [SupplyChain] Initiating restock order for 'Cold Coffee'

  *** EMERGENCY MODE ACTIVATED on KIOSK-01 ***
  *** Each user limited to 2 items ***
  *** All items are now FREE ***

  [Pricing] Strategy → Emergency Pricing (FREE)
  [CityMonitor] EMERGENCY MODE ACTIVATED — purchase limits enforced
```

**What happened internally:**
- `PurchaseCommand.execute()` fired `LowStockEvent` after stock dropped to 4
- `KioskInterface.purchase_item()` called `kiosk.check_and_activate_emergency()`
- `check_and_activate_emergency()` found stock ≤ 5 → called `_activate_emergency_mode()`
- `PricingContext.set_strategy(EmergencyPricing())` → all prices now 0.0
- `EventBus().publish(EmergencyModeActivatedEvent(...))` notified all city subscribers
- From this point, `can_user_purchase()` enforces the 2-item per-user limit

**User buying in emergency mode:**

```
KIOSK: KIOSK-01 [FoodKiosk] *** EMERGENCY MODE ***
  Your purchases: 0 | Remaining allowance: 2

  Item: Water Bottle
  *** EMERGENCY MODE — you can buy max 2 more item(s) ***
  How many? 3   → capped to 2 automatically

  [UPI API] Paying Rs.0.00 to user03@upi    ← FREE
  SUCCESS: Purchased 'Water Bottle' for Rs.0.00 via UPI
```

---

### Refund Simulation

**Goal:** User refunds a previous purchase.

```
KIOSK: KIOSK-01
  4. Refund

REFUND
  Your purchases at KIOSK-01:
    1. [A3F9B2C1] Water Bottle     Rs. 20.00  (2026-04-29)
    2. [7D4E1F88] Cold Coffee      Rs. 60.00  (2026-04-29)

  Enter Transaction ID to refund: A3F9B2C1

[KioskInterface] Refund txn: A3F9B2C1 | User: user_01
  [UPI API] Refunding Rs.20.00 to user01@paytm
  SUCCESS: Refunded 'Water Bottle' Rs.20.00 to 'user_01'

  Refund successful!
```

**What happened internally:**
- `RefundCommand.execute()` validated transaction ownership from `data.json`
- Called `payment_processor.refund_payment()` on the `UPIAdapter`
- Restored `item._stock += 1`
- Marked original transaction as `status: "REFUNDED"` in file
- Saved a new `REFUND` transaction record
- If restocking brought all items above the emergency threshold, emergency mode would be deactivated

---

### City Monitor Event Log

**Goal:** View all system events from the admin dashboard.

```
ADMIN MENU
  8. City Monitor Events

CITY MONITORING CENTER
  [CityMonitor] === EVENT LOG ===
  [2026-04-29 10:31:22] [KIOSK-01] LOW STOCK: 'Cold Coffee' has only 4 units left
  [2026-04-29 10:31:22] [KIOSK-01] EMERGENCY MODE ACTIVATED — purchase limits enforced
  [2026-04-29 10:45:11] [KIOSK-01] LOW STOCK: 'Water Bottle' has only 5 units left
  [2026-04-29 11:02:44] [KIOSK-01] RESTOCKED: 'Cold Coffee' +30 units
  [2026-04-29 11:03:09] [KIOSK-01] TRANSACTION FAILED: Payment failed

  Total events: 5
```

All events survive restarts — they are persisted to `data.json` by `CityMonitoringCenter.on_event()`.

---

### Admin: Change Kiosk Model

**Goal:** Convert a Food Kiosk into a Pharmacy Kiosk mid-operation.

```
ADMIN MENU → 6. Change Kiosk Model

  Current model: FoodKiosk
  New model:
    2. Pharmacy Kiosk
  Select: 2

  Kiosk 'KIOSK-01' changed from FoodKiosk → PharmacyKiosk.
```

The kiosk retains its ID, location, password, existing inventory, and hardware. Only the type is changed. The new `PharmacyKiosk` object is wired with the same hardware chain and inventory, then saved.

---

## Data Persistence

All system state lives in `persistence/data.json`. A sample structure:

```json
{
  "kiosks": {
    "KIOSK-01": {
      "kiosk_id": "KIOSK-01",
      "location": "Central Metro",
      "kiosk_type": "FoodKiosk",
      "password": "1234",
      "mode": "ACTIVE",
      "hardware_modules": ["dispenser", "motor", "basic_power", "refrigeration", "solar_power", "network"],
      "inventory": [
        { "type": "product", "product_id": "F001", "name": "Water Bottle", "price": 20.0, "stock": 48 },
        { "type": "product", "product_id": "F002", "name": "Cold Coffee",  "price": 60.0, "stock": 20, "requires_refrigeration": true }
      ]
    }
  },
  "transactions": [
    { "txn_id": "A3F9B2C1", "type": "PURCHASE", "kiosk_id": "KIOSK-01", "user_id": "user_01", "item": "Water Bottle", "amount": 20.0, "status": "REFUNDED" },
    { "txn_id": "REF-A3F9B2C1", "type": "REFUND", "kiosk_id": "KIOSK-01", "user_id": "user_01", "item": "Water Bottle", "amount": 20.0, "status": "SUCCESS" }
  ],
  "events": [
    "[2026-04-29 10:31:22] [KIOSK-01] LOW STOCK: 'Cold Coffee' has only 4 units left"
  ],
  "config": {}
}
```

---

## Running Tests

The test suite is in `test_aura_system.py` and covers all major flows programmatically (no interactive input required).

```bash
cd vending_machine
python3 test_aura_system.py
```

Test output is also written to `test_out.txt`. The tests exercise:

- Kiosk creation via `KioskFactory`
- Inventory operations: add, find, low stock detection
- Hardware decorator chain composition and capability reporting
- All three payment adapters
- Purchase, refund, restock commands with success and rollback cases
- Emergency mode activation and per-user purchase limit enforcement
- Dynamic pricing strategy switching
- Observer event bus and subscriber notification
- JSON persistence: save and restore
- Proxy access control

---

*AURA Retail OS — Smart City Modular Kiosk Platform*  
*Built as an academic design patterns demonstration project.*# oops_pro
