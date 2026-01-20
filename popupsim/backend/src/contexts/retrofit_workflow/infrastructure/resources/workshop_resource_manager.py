"""Workshop Resource Manager - wraps SimPy Resources for workshop capacity."""

from collections.abc import Callable
from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
import simpy


class WorkshopResourceManager:
    """Manages workshop SimPy resources.

    Each workshop has a SimPy Resource representing its retrofit bays.
    This manager provides a clean interface for workshop capacity management.

    Example:
        manager = WorkshopResourceManager(env, {'WS1': 2, 'WS2': 3})
        with manager.request_bay('WS1') as req:
            yield req  # Blocks if all bays busy
            # Retrofit wagon
        # Bay automatically released
    """

    def __init__(
        self,
        env: simpy.Environment,
        workshops: dict[str, int],
        event_publisher: Callable[[ResourceStateChangeEvent], None] | None = None,
    ):
        """Initialize workshop resource manager.

        Args:
            env: SimPy environment
            workshops: Dict mapping workshop_id -> capacity (number of bays)
            event_publisher: Optional callback to publish events
        """
        self.env = env
        self.workshops = workshops
        self.event_publisher = event_publisher

        # Create SimPy Resource for each workshop
        self.resources: dict[str, simpy.Resource] = {
            workshop_id: simpy.Resource(env, capacity=capacity) for workshop_id, capacity in workshops.items()
        }

    def request_bay(self, workshop_id: str) -> Generator[Any, Any, Any]:
        """Request a bay at workshop (blocks if all busy).

        Args:
            workshop_id: Workshop identifier

        Yields
        ------
            SimPy request

        Returns
        -------
            SimPy request object
        """
        if workshop_id not in self.resources:
            raise ValueError(f'Workshop {workshop_id} not found')

        resource = self.resources[workshop_id]

        # Capture state before
        busy_before = resource.count

        # Request bay - blocks if all busy
        req = resource.request()
        yield req

        # Capture state after
        busy_after = resource.count

        # Publish event
        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='workshop',
                    resource_id=workshop_id,
                    change_type='bay_occupied',
                    total_bays=int(resource.capacity),
                    busy_bays_before=busy_before,
                    busy_bays_after=busy_after,
                )
            )

        return req

    def release_bay(self, workshop_id: str, req: Any) -> None:
        """Release a bay at workshop.

        Args:
            workshop_id: Workshop identifier
            req: SimPy request object to release
        """
        if workshop_id not in self.resources:
            raise ValueError(f'Workshop {workshop_id} not found')

        resource = self.resources[workshop_id]

        # Capture state before
        busy_before = resource.count

        # Release bay
        resource.release(req)

        # Capture state after
        busy_after = resource.count

        # Publish event
        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='workshop',
                    resource_id=workshop_id,
                    change_type='bay_released',
                    total_bays=int(resource.capacity),
                    busy_bays_before=busy_before,
                    busy_bays_after=busy_after,
                )
            )

    def get_available_bays(self, workshop_id: str) -> int:
        """Get number of available bays.

        Args:
            workshop_id: Workshop identifier

        Returns
        -------
            Number of available bays
        """
        if workshop_id not in self.resources:
            return 0

        resource = self.resources[workshop_id]
        available = resource.capacity - resource.count
        return int(available)

    def get_capacity(self, workshop_id: str) -> int:
        """Get total capacity of workshop.

        Args:
            workshop_id: Workshop identifier

        Returns
        -------
            Total number of bays
        """
        capacity = self.workshops.get(workshop_id, 0)
        return int(capacity) if isinstance(capacity, (int, float)) else 0

    def get_utilization(self, workshop_id: str) -> float:
        """Get workshop utilization percentage.

        Args:
            workshop_id: Workshop identifier

        Returns
        -------
            Utilization as percentage (0-100)
        """
        if workshop_id not in self.resources:
            return 0.0

        resource = self.resources[workshop_id]
        if resource.capacity == 0:
            return 0.0

        return (resource.count / resource.capacity) * 100.0

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all workshops.

        Returns
        -------
            Dict mapping workshop_id -> metrics
        """
        return {
            workshop_id: {
                'capacity': self.get_capacity(workshop_id),
                'available': self.get_available_bays(workshop_id),
                'busy': self.resources[workshop_id].count,
                'utilization_percent': self.get_utilization(workshop_id),
            }
            for workshop_id in self.workshops
        }
