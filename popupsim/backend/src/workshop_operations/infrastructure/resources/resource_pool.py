"""Generic resource pool with tracking capabilities."""

import logging
from typing import Any
from typing import Protocol

logger = logging.getLogger('ResourcePool')


class Trackable(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for trackable resources."""

    locomotive_id: str  # or worker_id, crane_id, etc.
    status: Any
    track_id: str | None


class ResourcePool:  # pylint: disable=too-few-public-methods
    """Generic resource pool with allocation tracking.

    Tracks resource state, location, and utilization for any resource type
    (locomotives, workers, cranes, etc.).
    """

    def __init__(self, sim: Any, resources: list[Trackable], name: str = 'ResourcePool') -> None:
        self.sim = sim
        self.name = name
        # Support different ID attributes (locomotive_id, worker_id, etc.)
        self.all_resources: dict[str, Trackable] = {
            getattr(r, 'locomotive_id', getattr(r, 'worker_id', getattr(r, 'id', str(r)))): r for r in resources
        }
        self.store: Any = sim.create_store(capacity=len(resources))

        # Tracking state
        self.allocated: dict[str, float] = {}  # resource_id -> allocation_time
        # (time, resource_id, action, location)
        self.allocation_history: list[tuple[float, str, str, str | None]] = []

        for resource_id, r in self.all_resources.items():
            self.store.put(r)
            self._track_event(resource_id, 'initialized', r.track)

        logger.info('Initialized %s with %d resources', name, len(resources))

    def get(self) -> Any:
        """Get resource from pool (blocks until available)."""
        return self.store.get()

    def put(self, resource: Trackable) -> Any:
        """Return resource to pool."""
        return self.store.put(resource)

    def track_allocation(self, resource_id: str) -> None:
        """Track resource allocation."""
        self.allocated[resource_id] = self.sim.current_time()
        resource = self.all_resources[resource_id]
        self._track_event(resource_id, 'allocated', resource.track)

    def track_release(self, resource_id: str) -> None:
        """Track resource release."""
        if resource_id in self.allocated:
            del self.allocated[resource_id]
        resource = self.all_resources[resource_id]
        self._track_event(resource_id, 'released', resource.track)

    def _track_event(self, resource_id: str, action: str, location: str | None) -> None:
        """Record tracking event."""
        self.allocation_history.append((self.sim.current_time(), resource_id, action, location))

    def get_resource_state(self, resource_id: str) -> dict[str, Any]:
        """Get current state of a resource."""
        resource = self.all_resources[resource_id]
        is_allocated = resource_id in self.allocated
        return {
            'id': resource_id,
            'status': getattr(resource, 'status', 'unknown'),
            'location': getattr(resource, 'track_id', None),
            'allocated': is_allocated,
            'allocated_since': self.allocated.get(resource_id),
        }

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Get state of all resources."""
        return {rid: self.get_resource_state(rid) for rid in self.all_resources}

    def get_available_count(self) -> int:
        """Get number of available resources."""
        return len(self.all_resources) - len(self.allocated)

    def get_utilization(self, total_time: float) -> dict[str, float]:
        """Calculate utilization per resource."""
        utilization = {}
        for resource_id in self.all_resources:
            allocated_time = 0.0
            last_alloc = None

            for time, rid, action, _ in self.allocation_history:
                if rid == resource_id:
                    if action == 'allocated':
                        last_alloc = time
                    elif action == 'released' and last_alloc is not None:
                        allocated_time += time - last_alloc
                        last_alloc = None

            # Handle still-allocated resources
            if resource_id in self.allocated:
                allocated_time += total_time - self.allocated[resource_id]

            utilization[resource_id] = (allocated_time / total_time * 100) if total_time > 0 else 0.0

        return utilization
