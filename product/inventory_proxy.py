"""
DESIGN PATTERN: Proxy (Structural)
File: product/secure_inventory_proxy.py
Purpose: Controls access to Inventory operations based on user role.

         Adds a security layer between client and Inventory.
         Also logs all access attempts for auditing purposes.
"""

from datetime import datetime
from product.inventory import Inventory


class SecureInventoryProxy:
    """
    PROXY CLASS:
    Wraps the Inventory object and enforces role-based access control.

    Responsibilities:
    - Restrict sensitive operations (e.g., restocking)
    - Log all access attempts
    """

    def __init__(self, inventory: Inventory, role: str):
        self._inventory_ref = inventory
        self._user_role     = role
        self._audit_log     = []

    def _log_access(self, action: str, outcome: str):
        """
        Internal helper to record access attempts.
        """
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "role":      self._user_role,
            "operation": action,
            "status":    outcome
        })

    def restock(self, item_name: str, quantity: int) -> bool:
        """
        Allows restocking only if user has admin role.
        """
        if self._user_role != "admin":
            self._log_access(f"restock {item_name}", "DENIED")
            return False

        success = self._inventory_ref.restock(item_name, quantity)
        self._log_access(
            f"restock {item_name}",
            "SUCCESS" if success else "FAILED"
        )
        return success

    def get_all_items(self) -> list:
        """
        Read-only access to inventory items (allowed for all roles).
        """
        self._log_access("get_all_items", "SUCCESS")
        return self._inventory_ref.get_all_items()

    def get_access_log(self) -> list:
        """
        Returns audit trail of all operations performed via proxy.
        """
        return self._audit_log