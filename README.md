# 🚀 Aura Retail OS

### Modular Smart Kiosk Platform (Path B – IT620 OOP Project)

---

## 📌 Overview

**Aura Retail OS** is a modular, scalable, and extensible kiosk operating system designed to replace rigid monolithic vending machines.

This system enables:

* 🔌 Plug-and-play hardware modules
* 💳 Multiple payment integrations (UPI, Card, Wallet)
* 📦 Flexible inventory with nested bundles
* 🧩 Clean architecture using design patterns

---

## 🎯 Project Objective

The goal of this project is to build a **modular kiosk platform** where:

* New hardware can be added without changing existing code
* Payment providers can be switched dynamically
* Inventory supports complex bundle structures
* System remains scalable and maintainable

---

## 🧠 Design Patterns Implemented

| Pattern      | Purpose                           | Example                 |
| ------------ | --------------------------------- | ----------------------- |
| 🔌 Adapter   | Integrates different payment APIs | UPIAdapter, CardAdapter |
| 🧩 Decorator | Adds hardware dynamically         | RefrigerationModule     |
| 🌳 Composite | Nested inventory structure        | ProductBundle           |
| 🏭 Factory   | Creates fully configured kiosks   | KioskFactory            |
| 🎭 Facade    | Simplifies system interaction     | KioskInterface          |
| 🔒 Singleton | Global system state               | CentralRegistry         |

---

## 🏗️ System Architecture

The system is divided into multiple subsystems:

### 🔹 1. Kiosk Core System

Handles kiosk operations, modes, and coordination.

### 🔹 2. Inventory System

Manages products, bundles, pricing, and stock.

### 🔹 3. Payment System

Supports multiple payment providers via adapters.

### 🔹 4. Hardware Abstraction Layer

Controls physical hardware modules using decorators.

### 🔹 5. Central Registry

Maintains system-wide logs and persistence.

---

## 📂 Project Structure

```
oops_pro/
│
├── core/                # Core logic (Kiosk, Registry, Interface)
├── hardware/            # Dispenser + Decorator modules + Sensors
├── payment/             # Adapter pattern + Payment APIs
├── product/             # Product, Bundle, Inventory
├── pattern/             # Design pattern implementations
├── kiosks/              # Specific kiosk types
├── persistence/         # Saved data
├── main.py              # Simulation entry point
└── README.md
```

---

## ⚙️ Installation & Setup

### 🔹 Prerequisites

* Python 3.8+

### 🔹 Clone Repository

```bash
git clone https://github.com/Shiroilt/oops_pro.git
cd oops_pro
```

---

## ▶️ Running the Project

Run the simulation:

```bash
python main.py
```

---

## 🎬 Simulation Scenarios

The system demonstrates real-world working scenarios:

---

### 🔹 1. Adapter Pattern – Payment Integration

* Food kiosk uses **UPI**
* Pharmacy kiosk uses **Card**
* Payment is switched at runtime

✔ Output:

```
SUCCESS: 'Water Bottle' purchased for Rs.20.00 via UPI System
SUCCESS: 'Chips' purchased for Rs.25.00 via Card Gateway
[NOTE] Payment switched from UPI to Card — kiosk logic unchanged.
```

---

### 🔹 2. Decorator Pattern – Hardware Modules

* Base hardware is extended dynamically:

  * Refrigeration ❄️
  * Solar ☀️
  * Network 🌐

✔ Output:

```
Capabilities: ['dispenser', 'motor', 'basic_power']
Capabilities: [..., 'refrigeration']
Capabilities: [..., 'solar_power']
Capabilities: [..., 'network']
```

---

### 🔹 3. Composite Pattern – Inventory Bundles

* Bundles can contain products or other bundles

✔ Output:

```
[Bundle] Emergency Relief Kit — Rs.214.41 (15% off)
Available Stock: 20
```

---

### 🔹 4. Factory Pattern – Kiosk Creation

* Entire kiosk setup created using one method

✔ Output:

```
[KioskFactory] EmergencyKiosk created
SUCCESS: 'Ration Pack' purchased
```

---

### 🔹 5. Singleton Pattern – Central Registry

* Logs all transactions centrally

✔ Output:

```
[CentralRegistry] === SYSTEM SUMMARY ===
Total transactions: 6
```

---

## 🧪 Code Examples

### Adapter Pattern

```python
class UPIAdapter(PaymentProcessor):
    def process_payment(self, amount, user_id):
        return self._upi_service.initiate_upi_payment(self._vpa, amount)
```

---

### Decorator Pattern

```python
class RefrigerationModule(HardwareDecorator):
    def get_capabilities(self):
        return self._hardware.get_capabilities() + ["refrigeration"]
```

---

### Composite Pattern

```python
def get_price(self):
    total = sum(item.get_price() for item in self._items)
    return total * (1 - self.discount_pct / 100)
```

---

## 📊 Class Diagram

📌 View Diagram:
👉 Class_Diagram.jpeg

---

## 📸 Simulation Output

The system produces detailed console output demonstrating:

* Payment processing
* Hardware module stacking
* Inventory hierarchy
* Kiosk creation
* Transaction logging

---

## 👥 Team – Tech Titans

* 👑 Prajapati Darshankumar (Group Leader)
* Harsh Abhichandani
* Jayswal Mayank
* Soni Shashwat

---

## 📌 Conclusion

Aura Retail OS successfully demonstrates:

* Modular hardware integration
* Dynamic payment switching
* Flexible inventory design
* Scalable and maintainable architecture

The system fully satisfies **Path B requirements** using real-world design patterns.

---

## 🚀 Future Improvements

* Web dashboard UI
* Real-time monitoring
* Cloud-based system
* AI-driven inventory prediction

---

## 📎 License

This project is developed for academic purposes (IT620 OOP).

---
