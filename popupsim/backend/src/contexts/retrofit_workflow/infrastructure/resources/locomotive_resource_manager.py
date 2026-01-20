"""Locomotive Resource Manager - wraps SimPy Store for locomotive pool."""

from collections.abc import Callable
from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
import simpy


class LocomotiveResourceManager:
    """Manages locomotive pool using SimPy Store.

    SimPy Store provides natural FIFO queuing for locomotives.
    When all locomotives are allocated, requests automatically queue.

    Example:
        manager = LocomotiveResourceManager(env, [loco1, loco2])
        loco = yield from manager.allocate()
        # Use locomotive
        yield from manager.release(loco)
    """

    def __init__(
        self,
        env: simpy.Environment,
        locomotives: list[Locomotive],
        event_publisher: Callable[[ResourceStateChangeEvent], None] | None = None,
    ):
        """Initialize locomotive resource manager.

        Args:
            env: SimPy environment
            locomotives: List of locomotive entities
            event_publisher: Optional callback to publish events
        """
        self.env = env
        self.locomotives = locomotives
        self.event_publisher = event_publisher

        # Use simple Store for FIFO allocation
        self.store: simpy.Store = simpy.Store(env, capacity=len(locomotives))
        for loco in locomotives:
            self.store.put(loco)

        # Track allocated locomotives
        self._allocated: set[str] = set()
        self._workshop_pickup_pending: int = 0

    def allocate(self, purpose: str = 'general') -> Generator[Any, Any, Locomotive]:
        """Allocate a locomotive (blocks if none available).

        Args:
            purpose: Purpose description (for tracking)

        Yields
        ------
            SimPy event

        Returns
        -------
            Allocated locomotive
        """
        if purpose == 'workshop_pickup':
            self._workshop_pickup_pending += 1

        busy_before = len(self._allocated)

        # Get locomotive from store (FIFO)
        loco: Locomotive = yield self.store.get()
        self._allocated.add(loco.id)

        if purpose == 'workshop_pickup':
            self._workshop_pickup_pending = max(0, self._workshop_pickup_pending - 1)

        busy_after = len(self._allocated)

        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='locomotive',
                    resource_id=f'pool_{purpose}',
                    change_type='allocated',
                    total_count=len(self.locomotives),
                    busy_count_before=busy_before,
                    busy_count_after=busy_after,
                )
            )

        return loco

    def release(self, loco: Locomotive, purpose: str = 'general') -> Generator[Any, Any]:
        """Release locomotive back to pool.

        Args:
            loco: Locomotive to release
            purpose: Purpose description (for tracking)

        Yields
        ------
            SimPy event
        """
        busy_before = len(self._allocated)

        if loco.id in self._allocated:
            self._allocated.remove(loco.id)

        busy_after = len(self._allocated)

        # Return to store
        yield self.store.put(loco)

        if self.event_publisher:
            self.event_publisher(
                ResourceStateChangeEvent(
                    timestamp=self.env.now,
                    resource_type='locomotive',
                    resource_id=f'pool_{purpose}',
                    change_type='released',
                    total_count=len(self.locomotives),
                    busy_count_before=busy_before,
                    busy_count_after=busy_after,
                )
            )

    def get_total_count(self) -> int:
        """Get total number of locomotives.

        Returns
        -------
            Total locomotive count
        """
        return len(self.locomotives)

    def get_available_count(self) -> int:
        """Get number of available locomotives.

        Returns
        -------
            Number of locomotives in store
        """
        return len(self.store.items)

    def get_allocated_count(self) -> int:
        """Get number of allocated locomotives.

        Returns
        -------
            Number of locomotives currently allocated
        """
        return len(self._allocated)

    def get_utilization(self) -> float:
        """Get locomotive utilization percentage.

        Returns
        -------
            Utilization as percentage (0-100)
        """
        if not self.locomotives:
            return 0.0

        return (self.get_allocated_count() / len(self.locomotives)) * 100.0

    def get_metrics(self) -> dict[str, Any]:
        """Get locomotive pool metrics.

        Returns
        -------
            Dict with pool metrics
        """
        return {
            'total': self.get_total_count(),
            'available': self.get_available_count(),
            'allocated': self.get_allocated_count(),
            'utilization_percent': self.get_utilization(),
        }
