"""Coordinator configuration for retrofit workflow context."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from contexts.retrofit_workflow.application.config.publisher_config import PublisherConfig
from contexts.retrofit_workflow.application.config.queue_config import QueueConfig
from contexts.retrofit_workflow.application.config.service_config import ServiceConfig
from contexts.retrofit_workflow.application.interfaces.resource_interfaces import TrackSelector
from contexts.retrofit_workflow.application.interfaces.transport_interfaces import LocomotiveManager
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from contexts.retrofit_workflow.domain.services.track_selection_service import TrackSelectionService
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
import simpy


@dataclass
class CoordinatorConfig:
    """Main configuration for coordinators."""

    env: simpy.Environment
    queues: QueueConfig
    services: ServiceConfig
    publishers: PublisherConfig
    locomotive_manager: LocomotiveManager
    track_selector: TrackSelector
    scenario: Any

    def validate(self) -> None:
        """Validate coordinator configuration."""
        if not self.env:
            raise ValueError('SimPy environment is required')
        if not self.queues:
            raise ValueError('QueueConfig is required')
        if not self.services:
            raise ValueError('ServiceConfig is required')
        if not self.publishers:
            raise ValueError('PublisherConfig is required')
        if not self.locomotive_manager:
            raise ValueError('LocomotiveManager is required')
        if not self.track_selector:
            raise ValueError('TrackSelector is required')

        # Validate nested configs
        self.services.validate()

    @property
    def current_time(self) -> float:
        """Get current simulation time."""
        return self.env.now


@dataclass
class ArrivalCoordinatorConfig:
    """Configuration for ArrivalCoordinator."""

    env: simpy.Environment
    collection_queue: simpy.FilterStore
    event_publisher: Callable[[WagonJourneyEvent], None] | None = None


@dataclass
class TransportCoordinatorConfig:
    """Configuration for TransportCoordinator."""

    env: simpy.Environment
    move_time: float = 1.0
    coupling_time: float = 0.5


@dataclass
class CollectionCoordinatorConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for CollectionCoordinator."""

    env: simpy.Environment
    collection_queue: simpy.FilterStore
    retrofit_queue: simpy.FilterStore
    locomotive_manager: LocomotiveResourceManager
    track_selector: TrackSelectionService
    batch_service: BatchFormationService
    route_service: RouteService
    scenario: Any
    wagon_event_publisher: Callable[[WagonJourneyEvent], None] | None = None
    loco_event_publisher: Callable[[LocomotiveMovementEvent], None] | None = None
    batch_event_publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None = (
        None
    )


@dataclass
class WorkshopCoordinatorConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for WorkshopCoordinator."""

    env: simpy.Environment
    workshops: dict[str, Any]
    retrofit_queue: simpy.FilterStore
    retrofitted_queue: simpy.FilterStore
    locomotive_manager: LocomotiveResourceManager
    route_service: RouteService
    batch_service: BatchFormationService
    scenario: Any
    wagon_event_publisher: Callable[[WagonJourneyEvent], None] | None = None
    loco_event_publisher: Callable[[LocomotiveMovementEvent], None] | None = None


@dataclass
class ParkingCoordinatorConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for ParkingCoordinator."""

    env: simpy.Environment
    retrofitted_queue: simpy.FilterStore
    locomotive_manager: LocomotiveResourceManager
    track_selector: TrackSelectionService
    batch_service: BatchFormationService
    route_service: RouteService
    scenario: Any
    wagon_event_publisher: Callable[[WagonJourneyEvent], None] | None = None
    loco_event_publisher: Callable[[LocomotiveMovementEvent], None] | None = None
    batch_event_publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None = (
        None
    )
    # Strategy configuration
    strategy: str = 'opportunistic'  # 'opportunistic' or 'smart_accumulation'
    normal_threshold: float = 0.3  # 30% of retrofitted track capacity for smart_accumulation
    critical_threshold: float = 0.8  # 80% of retrofitted track capacity
    idle_check_interval: float = 1.0  # minutes
    retrofitted_track_capacity: float = 200.0  # meters
