"""
DESIGN PATTERN: Singleton
File: core/central_registry.py
Purpose: One global registry for all kiosk configuration, status, and transaction history.
"""

import json
import os


class CentralRegistry:
    """
    Singleton class — only one instance exists across the entire system.
    Stores global config, kiosk status, and transaction logs.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._kiosk_status = {}
            cls._instance._transaction_log = []
        return cls._instance

    # ── Config ────────────────────────────────────────────────────────────────

    def set_config(self, key: str, value):
        self._config[key] = value

    def get_config(self, key: str, default=None):
        return self._config.get(key, default)

    # ── Kiosk Status ──────────────────────────────────────────────────────────

    def update_kiosk_status(self, kiosk_id: str, status: dict):
        self._kiosk_status[kiosk_id] = status

    def get_kiosk_status(self, kiosk_id: str) -> dict:
        return self._kiosk_status.get(kiosk_id, {})

    def get_all_kiosk_statuses(self) -> dict:
        return dict(self._kiosk_status)

    # ── Transaction Log ───────────────────────────────────────────────────────

    def log_transaction(self, txn: dict):
        self._transaction_log.append(txn)

    def get_all_transactions(self) -> list:
        return list(self._transaction_log)

    def get_transactions_by_kiosk(self, kiosk_id: str) -> list:
        return [t for t in self._transaction_log if t.get("kiosk_id") == kiosk_id]

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_to_file(self, path: str = "persistence/data.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "config": self._config,
            "kiosk_status": self._kiosk_status,
            "transactions": self._transaction_log,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[CentralRegistry] State saved to {path}")

    def load_from_file(self, path: str = "persistence/data.json"):
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self._config = data.get("config", {})
            self._kiosk_status = data.get("kiosk_status", {})
            self._transaction_log = data.get("transactions", [])
            print(f"[CentralRegistry] State loaded from {path}")
        else:
            print(f"[CentralRegistry] No saved state found at {path}")

    def display_summary(self):
        print("\n[CentralRegistry] === SYSTEM SUMMARY ===")
        print(f"  Config entries    : {len(self._config)}")
        print(f"  Kiosks registered : {len(self._kiosk_status)}")
        print(f"  Total transactions: {len(self._transaction_log)}")
        for txn in self._transaction_log:
            print(f"    [{txn.get('txn_id', '?')}] {txn.get('item')} "
                  f"Rs.{txn.get('amount')} via {txn.get('provider')} — {txn.get('status')}")
