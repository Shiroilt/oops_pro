"""
File: persistence/file_handler.py
Purpose: Handles all save/load operations for the system.
         Persists inventory, transactions, and kiosk config to data.json.
         All operations are atomic — load → modify → save.
"""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


class FileHandler:
    """
    Manages reading and writing system state to data.json.
    Saves: kiosk configs, inventory, hardware modules, transactions.
    """

    @staticmethod
    def load() -> dict:
        """Load full system state from JSON. Returns empty structure if no file."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return FileHandler._empty()
        return FileHandler._empty()

    @staticmethod
    def save(data: dict):
        """Save full system state to JSON."""
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _empty() -> dict:
        return {
            "kiosks":       {},
            "transactions": [],
            "events":       [],
            "config":       {},
        }

    @staticmethod
    def save_kiosk(kiosk_id: str, kiosk_data: dict):
        """Add or update a single kiosk in the file."""
        data = FileHandler.load()
        data.setdefault("kiosks", {})[kiosk_id] = kiosk_data
        FileHandler.save(data)

    @staticmethod
    def load_kiosks() -> dict:
        """Return all saved kiosks."""
        return FileHandler.load().get("kiosks", {})

    @staticmethod
    def save_transaction(txn: dict):
        """Append a single transaction record."""
        data = FileHandler.load()
        data["transactions"].append(txn)
        FileHandler.save(data)

    @staticmethod
    def load_transactions() -> list:
        """Return all saved transactions."""
        return FileHandler.load().get("transactions", [])

    @staticmethod
    def save_event(event_str: str):
        """Append a single event record to the log."""
        data = FileHandler.load()
        if "events" not in data:
            data["events"] = []
        data["events"].append(event_str)
        FileHandler.save(data)

    @staticmethod
    def load_events() -> list:
        """Return all saved events."""
        return FileHandler.load().get("events", [])

    @staticmethod
    def update_inventory(kiosk_id: str, inventory: list):
        """Update inventory list for a specific kiosk."""
        data = FileHandler.load()
        if kiosk_id in data.get("kiosks", {}):
            data["kiosks"][kiosk_id]["inventory"] = inventory
            FileHandler.save(data)

    @staticmethod
    def clear():
        """Wipe all saved data (useful for testing)."""
        FileHandler.save(FileHandler._empty())
        print("[FileHandler] All data cleared.")
