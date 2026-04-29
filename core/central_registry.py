"""
DESIGN PATTERN: Singleton
File: core/central_registry.py
Purpose: One global registry for all kiosk config, status, and event log.
         Auto-loads from file on first access.
         Only ONE instance ever exists system-wide (Singleton).
"""

from persistence.file_handler import FileHandler


class CentralRegistry:
    """
    Singleton: only one instance exists system-wide.
    Loads saved state on startup automatically.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        """Load saved state from file. Call once at startup."""
        if not self._initialized:
            saved = FileHandler.load()
            self._config = saved.get("config", {})
            self._kiosk_status = {}
            self._initialized = True
            print("[CentralRegistry] Initialized and state loaded.")

    def _ensure_init(self):
        if not self._initialized:
            self._config = {}
            self._kiosk_status = {}
            self._initialized = True

    # ── Config ────────────────────────────────────────────────────────────────

    def set_config(self, key: str, value):
        self._ensure_init()
        self._config[key] = value

    def get_config(self, key: str, default=None):
        self._ensure_init()
        return self._config.get(key, default)

    # ── Kiosk Status ──────────────────────────────────────────────────────────

    def update_kiosk_status(self, kiosk_id: str, status: dict):
        self._ensure_init()
        self._kiosk_status[kiosk_id] = status

    def get_kiosk_status(self, kiosk_id: str) -> dict:
        self._ensure_init()
        return self._kiosk_status.get(kiosk_id, {})

    def get_all_statuses(self) -> dict:
        self._ensure_init()
        return dict(self._kiosk_status)

    # ── Transactions (via FileHandler) ────────────────────────────────────────

    def get_all_transactions(self) -> list:
        return FileHandler.load_transactions()

    def get_transactions_by_kiosk(self, kiosk_id: str) -> list:
        return [t for t in FileHandler.load_transactions()
                if t.get("kiosk_id") == kiosk_id]

    def get_transactions_by_user(self, user_id: str) -> list:
        return [t for t in FileHandler.load_transactions()
                if t.get("user_id") == user_id
                and t.get("type") == "PURCHASE"
                and t.get("status") == "SUCCESS"]

    # ── Summary ───────────────────────────────────────────────────────────────

    def display_summary(self):
        self._ensure_init()
        txns = self.get_all_transactions()
        purchases = [t for t in txns if t.get("type") == "PURCHASE"]
        refunds   = [t for t in txns if t.get("type") == "REFUND"]
        restocks  = [t for t in txns if t.get("type") == "RESTOCK"]

        print("\n[CentralRegistry] === SYSTEM SUMMARY ===")
        print(f"  Kiosks active     : {len(self._kiosk_status)}")
        print(f"  Total purchases   : {len(purchases)}")
        print(f"  Total refunds     : {len(refunds)}")
        print(f"  Total restocks    : {len(restocks)}")
        print(f"  All transactions  : {len(txns)}")
        print(f"\n  Config keys       : {list(self._config.keys())}")
