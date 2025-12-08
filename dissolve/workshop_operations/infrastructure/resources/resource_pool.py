"""Generic resource pool with tracking capabilities."""

import logging
from typing import Any, Protocol

logger = logging.getLogger("ResourcePool")


class Trackable(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for trackable resources."""

    id: str
    status: Any
    track: str | None


class ResourcePool:  # pylint: disable=too-few-public-methods
    """Generic resource pool with allocation tracking.

    Tracks resource state, location, and utilization for any resource type
    (locomotives, workers, cranes, etc.).
    """

    def __init__(
        self, sim: Any, resources: list[Trackable], name: str = "ResourcePool"
    ) -> None:
        self.sim = sim
        self.name = name
        self.all_resources: dict[str, Trackable] = {r.id: r for r in resources}
        self.store: Any = sim.create_store(capacity=len(resources))

        # Incremental utilization tracking - O(1) updates
        self.allocated: dict[str, float] = {}  # resource_id -> allocation_time
        self.total_allocated_time: dict[str, float] = {r.id: 0.0 for r in resources}

        for r in self.all_resources.values():
            self.store.put(r)

        logger.info("Initialized %s with %d resources", name, len(resources))

    def get(self) -> Any:
        """Get resource from pool (blocks until available)."""
        logger.debug(
            "🚂 POOL: Requesting resource from %s (available=%d)",
            self.name,
            len(self.store.items),
        )
        return self.store.get()

    def put(self, resource: Trackable) -> Any:
        """Return resource to pool."""
        logger.debug("🔓 POOL: Returning resource %s to %s", resource.id, self.name)
        return self.store.put(resource)

    def track_allocation(self, resource_id: str) -> None:
        """Track resource allocation."""
        self.allocated[resource_id] = self.sim.current_time()
        logger.info(
            "✓ POOL: Allocated %s from %s (t=%.1f)",
            resource_id,
            self.name,
            self.sim.current_time(),
        )

    def track_release(self, resource_id: str) -> None:
        """Track resource release."""
        if resource_id not in self.allocated:
            logger.warning(
                "Attempting to release non-allocated resource: %s", resource_id
            )
            return
        allocation_duration = self.sim.current_time() - self.allocated[resource_id]
        self.total_allocated_time[resource_id] += allocation_duration
        del self.allocated[resource_id]
        logger.info(
            "🔓 POOL: Released %s to %s (t=%.1f)",
            resource_id,
            self.name,
            self.sim.current_time(),
        )

    def get_resource_state(self, resource_id: str) -> dict[str, Any]:
        """Get current state of a resource."""
        resource = self.all_resources[resource_id]
        is_allocated = resource_id in self.allocated
        return {
            "id": resource_id,
            "status": getattr(resource, "status", "unknown"),
            "location": getattr(resource, "track", None),
            "allocated": is_allocated,
            "allocated_since": self.allocated.get(resource_id),
        }

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Get state of all resources."""
        return {rid: self.get_resource_state(rid) for rid in self.all_resources}

    def get_available_count(self) -> int:
        """Get number of available resources."""
        return len(self.all_resources) - len(self.allocated)

    def get_utilization(self, total_time: float) -> dict[str, float]:
        """Calculate utilization per resource - O(n) complexity."""
        utilization = {}
        for resource_id in self.all_resources:
            allocated_time = self.total_allocated_time[resource_id]
            # Add current allocation if still allocated
            if resource_id in self.allocated:
                allocated_time += self.sim.current_time() - self.allocated[resource_id]
            utilization[resource_id] = (
                (allocated_time / total_time * 100) if total_time > 0 else 0.0
            )
        return utilization
