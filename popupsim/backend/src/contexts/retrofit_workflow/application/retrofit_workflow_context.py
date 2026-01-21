"""Retrofit wWrkflows Context - main orchestrator for all operations.

This superseeds the three separate contexts (yard, popup, shunting).
"""

from typing import Any

from contexts.retrofit_workflow.application.builders.operations_context_builder import RetrofitWorkshopContexttBuilder
from contexts.retrofit_workflow.application.config.coordinator_config import ArrivalCoordinatorConfig
from contexts.retrofit_workflow.application.config.coordinator_config import CollectionCoordinatorConfig
from contexts.retrofit_workflow.application.config.coordinator_config import ParkingCoordinatorConfig
from contexts.retrofit_workflow.application.config.coordinator_config import WorkshopCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.arrival_coordinator import ArrivalCoordinator
from contexts.retrofit_workflow.application.coordinators.collection_coordinator import CollectionCoordinator
from contexts.retrofit_workflow.application.coordinators.parking_coordinator import ParkingCoordinator
from contexts.retrofit_workflow.application.coordinators.workshop_coordinator import WorkshopCoordinator
from contexts.retrofit_workflow.application.event_collector import EventCollector
from contexts.retrofit_workflow.application.services.coordination_service import CoordinationService
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.services.coupling_validation_service import CouplingValidationService
from contexts.retrofit_workflow.domain.services.rake_formation_service import RakeFormationService
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from contexts.retrofit_workflow.domain.services.track_selection_service import TrackSelectionService
from contexts.retrofit_workflow.domain.services.workshop_assignment_service import WorkshopAssignmentService
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackResourceManager
from contexts.retrofit_workflow.infrastructure.resources.workshop_resource_manager import WorkshopResourceManager
import simpy


class RetrofitWorkshopContext:  # pylint: disable=too-many-instance-attributes
    """Retrofit workshop context.

    Single context superseeding:
    - YardOperationsContext (train arrival, classification)
    - PopUpRetrofitContext (workshop operations)
    - ShuntingOperationsContext (rake formation, transport)

    Architecture:
    - Coordinators: SimPy orchestration (arrival, collection, workshop, parking)
    - Domain Services: Pure business logic (batch formation, rake formation)
    - Resource Managers: SimPy resource wrappers

    Wagon flow:
    Train → Collection → Retrofit → Workshop → Retrofitted → Parking
    """

    def __init__(self, env: simpy.Environment, scenario: Any):
        """Initialize context.

        Args:
            env: SimPy environment
            scenario: Scenario configuration
        """
        self.env = env
        self.scenario = scenario

        # SimPy queues for wagon flow
        self.collection_queue: simpy.FilterStore = simpy.FilterStore(env)
        self.retrofit_queue: simpy.FilterStore = simpy.FilterStore(env)
        self.retrofitted_queue: simpy.FilterStore = simpy.FilterStore(env)

        # Domain entities
        self.workshops: dict[str, Workshop] = {}
        self.locomotives: list[Locomotive] = []

        # Resource managers
        self.workshop_resources: WorkshopResourceManager | None = None
        self.locomotive_manager: LocomotiveResourceManager | None = None
        self.track_manager: TrackResourceManager | None = None

        # Domain services
        self.coupling_validator = CouplingValidationService()
        self.rake_formation_service = RakeFormationService()
        self.batch_formation_service = BatchFormationService()
        self.route_service: RouteService | None = None
        self.track_selector: TrackSelectionService | None = None
        self.workshop_assignment_service: WorkshopAssignmentService | None = None

        # Event collection
        self.event_collector: EventCollector | None = None

        # Coordinators
        self.arrival_coordinator: ArrivalCoordinator | None = None
        self.collection_coordinator: CollectionCoordinator | None = None
        self.workshop_coordinator: WorkshopCoordinator | None = None
        self.parking_coordinator: ParkingCoordinator | None = None

        # Coordination state for priority management (parking has priority over workshop)
        self.parking_in_progress: bool = False
        self.retrofitted_accumulator: list[Any] = []  # Wagons waiting to be parked

    def initialize(self) -> None:
        """Initialize context from scenario using builder pattern."""
        builder = RetrofitWorkshopContexttBuilder(self.env, self.scenario)

        # Build components step by step
        builder.build_event_collector()
        builder.build_entities()
        builder.build_resource_managers()

        # Extract built components
        self.event_collector = builder.get_event_collector()
        self.workshops = builder.get_workshops()
        self.locomotives = builder.get_locomotives()
        self.workshop_resources = builder.get_workshop_resources()
        self.locomotive_manager = builder.get_locomotive_manager()

        # Build remaining components (simplified)
        self._build_remaining_components()

    def start_processes(self) -> None:
        """Start all coordinator processes."""
        if self.collection_coordinator:
            self.collection_coordinator.start()
        if self.workshop_coordinator:
            self.workshop_coordinator.start()
        if self.parking_coordinator:
            self.parking_coordinator.start()

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics from all components.

        Returns
        -------
        dict
            Combined metrics
        """
        metrics = {}

        # Workshop metrics
        if self.workshop_resources:
            metrics['workshops'] = self.workshop_resources.get_all_metrics()

        # Locomotive metrics
        if self.locomotive_manager:
            metrics['locomotives'] = self.locomotive_manager.get_metrics()

        # Track metrics
        if self.track_manager:
            metrics['tracks'] = self.track_manager.get_all_metrics()

        return metrics

    def export_events(self, output_dir: str) -> None:
        """Export collected events to files.

        Parameters
        ----------
        output_dir: str
            Directory to write event files
        """
        if self.event_collector:
            self.event_collector.export_all(output_dir)

    def cleanup(self) -> None:
        """Cleanup context resources."""

    def get_status(self) -> dict[str, Any]:
        """Get context status.

        Returns
        -------
        dict
            Status information
        """
        return {
            'workshops': len(self.workshops),
            'locomotives': len(self.locomotives),
            'status': 'ready',
        }

    def _build_remaining_components(self) -> None:
        """Build remaining components (simplified for now)."""
        self._build_track_and_route_services()
        self._build_coordinators()

    def _build_track_and_route_services(self) -> None:
        """Build track manager, route service, and track selector."""
        # Create track manager with all tracks
        track_capacities = {}
        for track_config in self.scenario.tracks:
            capacity = track_config.length * track_config.fillfactor
            track_capacities[track_config.id] = capacity
        self.track_manager = TrackResourceManager(
            self.env,
            track_capacities,
            event_publisher=self.event_collector.add_resource_event if self.event_collector else None,
        )

        # Create route service
        self.route_service = RouteService(self.scenario.routes)

        # Create track selector using SAME track instances from track_manager
        tracks_by_type: dict[str, list[Any]] = {}
        for track_config in self.scenario.tracks:
            track_type = track_config.type
            if track_type not in tracks_by_type:
                tracks_by_type[track_type] = []
            if self.track_manager:
                track = self.track_manager.get_track(track_config.id)
                if track:
                    tracks_by_type[track_type].append(track)

        self.track_selector = TrackSelectionService(tracks_by_type)
        self.workshop_assignment_service = WorkshopAssignmentService(dict(self.workshops))

    def _build_coordinators(self) -> None:
        """Build all coordinators."""
        coordination_service = CoordinationService()

        self._build_arrival_coordinator()
        self._build_collection_coordinator(coordination_service)
        self._build_workshop_coordinator(coordination_service)
        self._build_parking_coordinator(coordination_service)

    def _build_arrival_coordinator(self) -> None:
        """Build arrival coordinator."""
        arrival_config = ArrivalCoordinatorConfig(
            env=self.env,
            collection_queue=self.collection_queue,
            event_publisher=self.event_collector.add_wagon_event if self.event_collector else None,
        )
        self.arrival_coordinator = ArrivalCoordinator(arrival_config)

    def _build_collection_coordinator(self, coordination_service: CoordinationService) -> None:
        """Build collection coordinator."""
        if not self.locomotive_manager:
            raise RuntimeError('Locomotive manager not initialized')
        if not self.event_collector:
            raise RuntimeError('Event collector not initialized')

        collection_config = CollectionCoordinatorConfig(
            env=self.env,
            collection_queue=self.collection_queue,
            retrofit_queue=self.retrofit_queue,
            locomotive_manager=self.locomotive_manager,
            track_selector=self.track_selector,
            batch_service=self.batch_formation_service,
            route_service=self.route_service,
            scenario=self.scenario,
            wagon_event_publisher=self.event_collector.add_wagon_event,
            loco_event_publisher=self.event_collector.add_locomotive_event,
            batch_event_publisher=self.event_collector.add_batch_event,
        )
        self.collection_coordinator = CollectionCoordinator(collection_config, coordination_service)

    def _build_workshop_coordinator(self, coordination_service: CoordinationService) -> None:
        """Build workshop coordinator."""
        if not self.locomotive_manager or not self.event_collector:
            raise RuntimeError('Required managers not initialized')

        workshop_config = WorkshopCoordinatorConfig(
            env=self.env,
            workshops=self.workshops,
            retrofit_queue=self.retrofit_queue,
            retrofitted_queue=self.retrofitted_queue,
            locomotive_manager=self.locomotive_manager,
            route_service=self.route_service,
            batch_service=self.batch_formation_service,
            scenario=self.scenario,
            wagon_event_publisher=self.event_collector.add_wagon_event,
            loco_event_publisher=self.event_collector.add_locomotive_event,
        )
        self.workshop_coordinator = WorkshopCoordinator(workshop_config, coordination_service)
        self.workshop_coordinator.track_manager = self.track_manager

    def _build_parking_coordinator(self, coordination_service: CoordinationService) -> None:
        """Build parking coordinator."""
        if not self.locomotive_manager or not self.event_collector:
            raise RuntimeError('Required managers not initialized')

        # Get retrofitted track capacity
        retrofitted_track_capacity = 200.0  # Default
        for track_config in self.scenario.tracks:
            if track_config.type == 'retrofitted':
                retrofitted_track_capacity = track_config.length * track_config.fillfactor
                break

        # Get parking strategy configuration from scenario (with defaults)
        parking_config = ParkingCoordinatorConfig(
            env=self.env,
            retrofitted_queue=self.retrofitted_queue,
            locomotive_manager=self.locomotive_manager,
            track_selector=self.track_selector,
            batch_service=self.batch_formation_service,
            route_service=self.route_service,
            scenario=self.scenario,
            wagon_event_publisher=self.event_collector.add_wagon_event,
            loco_event_publisher=self.event_collector.add_locomotive_event,
            batch_event_publisher=self.event_collector.add_batch_event,
            strategy=getattr(self.scenario, 'parking_strategy', 'opportunistic'),
            normal_threshold=getattr(self.scenario, 'parking_normal_threshold', 0.3),
            critical_threshold=getattr(self.scenario, 'parking_critical_threshold', 0.8),
            idle_check_interval=getattr(self.scenario, 'parking_idle_check_interval', 1.0),
            retrofitted_track_capacity=retrofitted_track_capacity,
        )
        self.parking_coordinator = ParkingCoordinator(parking_config, coordination_service)
