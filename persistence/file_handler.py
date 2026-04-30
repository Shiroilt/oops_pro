"""
File: persistence/file_handler.py
Purpose: Responsible for handling all file-based persistence.
         Stores and retrieves kiosks, transactions, events, and configuration
         from a JSON file.
         
         Design Note:
         Every operation follows an atomic pattern:
         load → modify → save
"""

import json
import os

# Path to the JSON storage file
STORAGE_PATH = os.path.join(os.path.dirname(__file__), "data.json")


class FileHandler:
    """
    Utility class for managing persistent storage.

    Handles:
    - Kiosk configurations
    - Inventory data
    - Transactions
    - System events
    """

    @staticmethod
    def load() -> dict:
        """
        Read complete system data from JSON file.
        If file is missing or corrupted, return default structure.
        """
        if os.path.exists(STORAGE_PATH):
            with open(STORAGE_PATH, "r") as file_obj:
                try:
                    return json.load(file_obj)
                except json.JSONDecodeError:
                    return FileHandler._default_structure()
        return FileHandler._default_structure()

    @staticmethod
    def save(payload: dict):
        """
        Write entire system data to JSON file.
        """
        os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
        with open(STORAGE_PATH, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)

    @staticmethod
    def _default_structure() -> dict:
        """
        Returns base structure for empty storage.
        """
        return {
            "kiosks":       {},
            "transactions": [],
            "events":       [],
            "config":       {},
        }

    @staticmethod
    def save_kiosk(kiosk_key: str, kiosk_info: dict):
        """
        Insert or update a kiosk entry.
        """
        data_blob = FileHandler.load()
        data_blob.setdefault("kiosks", {})[kiosk_key] = kiosk_info
        FileHandler.save(data_blob)

    @staticmethod
    def load_kiosks() -> dict:
        """
        Fetch all stored kiosks.
        """
        return FileHandler.load().get("kiosks", {})

    @staticmethod
    def save_transaction(transaction_record: dict):
        """
        Add a new transaction entry.
        """
        data_blob = FileHandler.load()
        data_blob["transactions"].append(transaction_record)
        FileHandler.save(data_blob)

    @staticmethod
    def load_transactions() -> list:
        """
        Fetch all transaction records.
        """
        return FileHandler.load().get("transactions", [])

    @staticmethod
    def save_event(event_message: str):
        """
        Append an event log entry.
        """
        data_blob = FileHandler.load()
        if "events" not in data_blob:
            data_blob["events"] = []
        data_blob["events"].append(event_message)
        FileHandler.save(data_blob)

    @staticmethod
    def load_events() -> list:
        """
        Retrieve all event logs.
        """
        return FileHandler.load().get("events", [])

    @staticmethod
    def update_inventory(kiosk_key: str, item_list: list):
        """
        Replace inventory for a given kiosk.
        """
        data_blob = FileHandler.load()
        if kiosk_key in data_blob.get("kiosks", {}):
            data_blob["kiosks"][kiosk_key]["inventory"] = item_list
            FileHandler.save(data_blob)

    @staticmethod
    def clear():
        """
        Reset entire storage to default state.
        Useful for testing and debugging.
        """
        FileHandler.save(FileHandler._default_structure())
        print("[FileHandler] Storage reset completed.")