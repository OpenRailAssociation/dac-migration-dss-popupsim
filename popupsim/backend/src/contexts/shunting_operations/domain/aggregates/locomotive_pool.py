"""Locomotive pool aggregate."""

from typing import Any

from contexts.shunting_operations.domain.entities.shunting_locomotive import ShuntingLocomotive
from contexts.shunting_operations.domain.entities.shunting_locomotive import ShuntingStatus
from contexts.shunting_operations.domain.events.shunting_events import LocomotiveAllocatedEvent
from contexts.shunting_operations.domain.events.shunting_events import LocomotiveReleasedEvent
from contexts.shunting_operations.domain.value_objects.shunting_metrics import ShuntingMetrics
from pydantic import BaseModel
from pydantic import Field


class LocomotivePool(BaseModel):
    """Aggregate managing locomotive allocation and operations."""

    locomotives: list[ShuntingLocomotive] = Field(description='Available locomotives')
    allocated: dict[str, str] = Field(default_factory=dict, description='Allocated locomotives (loco_id -> requester)')
    metrics: ShuntingMetrics = Field(default_factory=ShuntingMetrics, description='Pool metrics')

    def allocate_locomotive(
        self, requester: str, current_time: float = 0.0
    ) -> tuple[ShuntingLocomotive | None, list[Any]]:
        """Allocate an available locomotive.

        Returns
        -------
            Tuple of (locomotive, domain_events)
        """
        available_loco = next((loco for loco in self.locomotives if loco.is_available()), None)

        if not available_loco:
            return None, []

        # Allocate locomotive
        self.allocated[available_loco.id.value] = requester
        available_loco.start_operation(ShuntingStatus.MOVING)

        # Create event
        event = LocomotiveAllocatedEvent(
            locomotive_id=available_loco.id.value,
            allocated_to=requester,
            track=available_loco.current_track,
            event_timestamp=current_time,
        )

        self.metrics.locomotives_allocated += 1

        return available_loco, [event]

    def release_locomotive(self, locomotive_id: str, current_time: float = 0.0) -> tuple[bool, list[Any]]:
        """Release an allocated locomotive.

        Returns
        -------
            Tuple of (success, domain_events)
        """
        if locomotive_id not in self.allocated:
            return False, []

        locomotive = next((loco for loco in self.locomotives if loco.id.value == locomotive_id), None)
        if not locomotive:
            return False, []

        requester = self.allocated.pop(locomotive_id)
        locomotive.complete_operation()

        # Create event
        event = LocomotiveReleasedEvent(
            locomotive_id=locomotive_id,
            released_from=requester,
            track=locomotive.current_track,
            event_timestamp=current_time,
        )

        return True, [event]

    def get_available_count(self) -> int:
        """Get number of available locomotives."""
        return sum(1 for loco in self.locomotives if loco.is_available())

    def get_utilization(self) -> float:
        """Get utilization percentage."""
        if not self.locomotives:
            return 0.0
        allocated_count = len(self.allocated)
        return (allocated_count / len(self.locomotives)) * 100.0
