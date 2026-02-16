"""SimPy transport adapter implementation."""

from collections.abc import Generator
from typing import Any

import simpy

from ...application.ports.transport_port import ResourceAllocationPort
from ...application.ports.transport_port import TransportPort
from ...domain.aggregates.batch_aggregate import BatchAggregate
from ...domain.entities.locomotive import Locomotive
from ...domain.services.route_service import RouteService
from ...infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager as LocomotiveManager
from ...infrastructure.resources.workshop_resource_manager import WorkshopResourceManager as WorkshopCapacityManager


class SimPyTransportAdapter(TransportPort):
    """SimPy implementation of transport operations."""

    def __init__(
        self,
        env: simpy.Environment,
        locomotive_manager: LocomotiveManager,
        route_service: RouteService,
        retrofitted_queue: simpy.FilterStore | None = None,
    ):
        self._env = env
        self._locomotive_manager = locomotive_manager
        self._route_service = route_service
        self._retrofitted_queue = retrofitted_queue

    def transport_batch_to_workshop(self, batch: BatchAggregate, workshop_id: str) -> Generator[Any, Any]:
        """Transport batch to workshop using SimPy."""
        # Allocate locomotive
        locomotive = yield from self._locomotive_manager.allocate()

        # Start transport in batch aggregate
        batch.start_transport(locomotive)

        # Simulate transport time (route-based)
        transport_time = self._calculate_transport_time(batch.total_length, workshop_id)
        yield self._env.timeout(transport_time)

        # Arrive at workshop
        batch.arrive_at_destination()

    def transport_batch_from_workshop(self, batch: BatchAggregate, destination: str) -> Generator[Any, Any]:
        """Transport batch from workshop using SimPy."""
        # Simulate transport time
        transport_time = self._calculate_transport_time(batch.total_length, destination)
        yield self._env.timeout(transport_time)

        # Move wagons to retrofitted queue
        if self._retrofitted_queue:
            for wagon in batch.wagons:
                wagon.move_to('retrofitted')
                self._retrofitted_queue.put(wagon)
        else:
            print('Transport adapter: ERROR - no retrofitted queue available!')

    def return_locomotive(self, locomotive: Locomotive, origin: str) -> Generator[Any, Any]:
        """Return locomotive to origin using SimPy."""
        return_time = self._calculate_return_time(origin)
        yield self._env.timeout(return_time)
        yield from self._locomotive_manager.release(locomotive)

    def _calculate_transport_time(self, batch_length: float, destination: str) -> float:
        """Calculate transport time using route service and batch length."""
        # Base time from route service
        base_time = self._route_service.get_retrofit_to_workshop_time(destination)
        # Add time based on batch length (longer batches take more time)
        length_factor = 1.0 + (batch_length / 100.0)  # 1% extra per 100m
        return base_time * length_factor

    def _calculate_return_time(self, origin: str) -> float:
        """Calculate locomotive return time based on origin."""
        # Use route service for proper return time calculation
        if origin == 'retrofitted':
            return self._route_service.get_duration('retrofitted', 'locoparking')
        if origin.startswith('WS'):
            return self._route_service.get_duration(origin, 'locoparking')
        return 15.0  # Default fallback


class SimPyResourceAdapter(ResourceAllocationPort):
    """SimPy implementation of resource allocation."""

    def __init__(
        self, locomotive_manager: LocomotiveManager, workshop_manager: WorkshopCapacityManager, env: simpy.Environment
    ):
        self._locomotive_manager = locomotive_manager
        self._workshop_manager = workshop_manager
        self.env = env

    def allocate_locomotive(self) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive using SimPy Store."""
        loco: Locomotive = yield from self._locomotive_manager.allocate()
        return loco

    def release_locomotive(self, locomotive: Locomotive) -> Generator[Any, Any]:
        """Release locomotive using SimPy Store."""
        yield from self._locomotive_manager.release(locomotive)

    def allocate_workshop_capacity(self, workshop_id: str, required_capacity: int) -> Generator[Any, Any]:
        """Allocate workshop capacity using SimPy Resource."""
        # Request the required number of bays
        for _ in range(required_capacity):
            yield from self._workshop_manager.request_bay(workshop_id)

    def release_workshop_capacity(self, workshop_id: str, capacity: int) -> Generator[Any, Any]:  # noqa: ARG002
        """Release workshop capacity using SimPy Resource."""
        # Note: WorkshopResourceManager doesn't have release_capacity method
        # This is a placeholder - actual implementation depends on how capacity is tracked
        yield self.env.timeout(0)  # Ensure generator behavior
