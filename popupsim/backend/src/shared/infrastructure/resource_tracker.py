"""Generic resource status tracking service."""

from enum import Enum
from typing import TypeVar

StatusType = TypeVar("StatusType", bound=Enum)


class ResourceTracker[StatusType: Enum]:
    """Generic tracker for any resource with any status enum."""

    def __init__(self) -> None:
        self.status_history: dict[str, list[tuple[float, StatusType]]] = {}
        self.current_status: dict[str, StatusType] = {}

    def record_status_change(
        self, resource_id: str, sim_time: float, status: StatusType
    ) -> None:
        """Record resource status change."""
        if resource_id not in self.status_history:
            self.status_history[resource_id] = []

        self.status_history[resource_id].append((sim_time, status))
        self.current_status[resource_id] = status

    def get_status_history(self, resource_id: str) -> list[tuple[float, StatusType]]:
        """Get status history for resource."""
        return self.status_history.get(resource_id, [])

    def get_current_status(self, resource_id: str) -> StatusType | None:
        """Get current status for resource."""
        return self.current_status.get(resource_id)
