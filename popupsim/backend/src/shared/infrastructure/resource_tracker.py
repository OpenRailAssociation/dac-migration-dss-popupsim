"""Generic resource status tracking service."""

from enum import Enum
from typing import TypeVar

STATUSTYPE = TypeVar('STATUSTYPE', bound=Enum)


class ResourceTracker[STATUSTYPE: Enum]:
    """Generic tracker for any resource with any status enum."""

    def __init__(self) -> None:
        self.status_history: dict[str, list[tuple[float, STATUSTYPE]]] = {}
        self.current_status: dict[str, STATUSTYPE] = {}

    def record_status_change(self, resource_id: str, sim_time: float, status: STATUSTYPE) -> None:
        """Record resource status change."""
        if resource_id not in self.status_history:
            self.status_history[resource_id] = []

        self.status_history[resource_id].append((sim_time, status))
        self.current_status[resource_id] = status

    def get_status_history(self, resource_id: str) -> list[tuple[float, STATUSTYPE]]:
        """Get status history for resource."""
        return self.status_history.get(resource_id, [])

    def get_current_status(self, resource_id: str) -> STATUSTYPE | None:
        """Get current status for resource."""
        return self.current_status.get(resource_id)
