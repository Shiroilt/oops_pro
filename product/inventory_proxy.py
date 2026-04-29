from datetime import datetime
from product.inventory import Inventory

class SecureInventoryProxy:
    """Proxy pattern implementation to secure access to the Inventory."""
    
    def __init__(self, inventory: Inventory, role: str):
        self._inventory = inventory
        self._role = role
        self._access_log = []

    def _log_access(self, operation: str, status: str):
        self._access_log.append({
            "timestamp": datetime.now().isoformat(),
            "role": self._role,
            "operation": operation,
            "status": status
        })

    def restock(self, item_name: str, quantity: int) -> bool:
        if self._role != "admin":
            self._log_access(f"restock {item_name}", "DENIED")
            return False
            
        result = self._inventory.restock(item_name, quantity)
        self._log_access(f"restock {item_name}", "SUCCESS" if result else "FAILED")
        return result

    def get_all_items(self) -> list:
        self._log_access("get_all_items", "SUCCESS")
        return self._inventory.get_all_items()

    def get_access_log(self) -> list:
        return self._access_log
