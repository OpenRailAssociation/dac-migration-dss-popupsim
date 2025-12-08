"""Workshop Operations Context - implements BoundedContextPort."""

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from analytics.application.metrics_aggregator import SimulationMetrics
from analytics.domain.collectors.locomotive_collector import LocomotiveCollector
from analytics.domain.collectors.wagon_collector import WagonCollector
from analytics.domain.collectors.wagon_movement_collector import WagonMovementCollector
from analytics.domain.events.location_events import WagonLocationChangedEvent
from analytics.domain.events.simulation_events import WagonArrivedEvent
from analytics.domain.value_objects.timestamp import Timestamp
from configuration.domain.models.scenario import Scenario
from popup_retrofit.application.popup_context import PopUpRetrofitContext
from shunting_operations.application.shunting_context import ShuntingOperationsContext
from yard_operations.application.yard_operations_config import YardOperationsConfig
from yard_operations.application.yard_operations_context import YardOperationsContext
from yard_operations.infrastructure.parking_coordinator import ParkingSimPyCoordinator

from workshop_operations.application.coordinators.train_arrival_coordinator import (
    TrainArrivalCoordinator,
)
from workshop_operations.application.coordinators.wagon_pickup_coordinator import (
    WagonPickupCoordinator,
)
from workshop_operations.application.coordinators.workshop_processing_coordinator import (
    WorkshopProcessingCoordinator,
)
from workshop_operations.application.factories.entity_factory import EntityFactory
from workshop_operations.domain.entities.track import TrackType
from workshop_operations.domain.entities.wagon import CouplerType, Wagon, WagonStatus
from workshop_operations.domain.entities.workshop import Workshop
from workshop_operations.domain.services.scenario_domain_validator import (
    ScenarioDomainValidator,
)
from workshop_operations.domain.services.wagon_operations import (
    WagonSelector,
    WagonStateManager,
)
from workshop_operations.domain.services.workshop_operations import WorkshopDistributor
from workshop_operations.infrastructure.resources.track_capacity_manager import (
    TrackCapacityManager,
)
from workshop_operations.infrastructure.resources.workshop_capacity_manager import (
    WorkshopCapacityManager,
)

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession

logger = logging.getLogger(__name__)


class WorkshopOperationsContext:  # pylint: disable=too-many-instance-attributes
    """Workshop operations as bounded context."""

    def __init__(
        self,
        scenario: Scenario,
        shunting_context: ShuntingOperationsContext | None = None,
        yard_context: YardOperationsContext | None = None,
    ) -> None:
        """Initialize workshop operations context.

        Parameters
        ----------
        scenario : Scenario
            Simulation scenario configuration
        shunting_context : ShuntingOperationsContext | None
            Shunting operations context (created if not provided)
        yard_context : YardOperationsContext | None
            Yard operations context (created if not provided)
        """
        self.scenario = scenario
        self.sim: Any = None  # Set during initialize()
        self.session: SimulationSession | None = None

        # Initialize or inject shunting context
        if shunting_context is None:
            shunting_context = ShuntingOperationsContext(scenario)
        self._shunting_operations = shunting_context

        # Store yard context (will be set in initialize if not provided)
        self._yard_context_injected = yard_context

        self.trains = scenario.trains or []
        self.wagons: list[Wagon] = []
        self.rejected_wagons: list[Wagon] = []
        self.workshops: list[Workshop] = [
            EntityFactory.create_workshop(dto) for dto in (scenario.workshops or [])
        ]

        # Domain services (no simulation dependencies)
        self.wagon_selector = WagonSelector()
        self.wagon_state = WagonStateManager()
        self.workshop_distributor = WorkshopDistributor()

        # Extract parking and retrofitted tracks
        self.parking_tracks = [
            t for t in (scenario.tracks or []) if t.type == TrackType.PARKING
        ]
        self.retrofitted_tracks = [
            t for t in (scenario.tracks or []) if t.type == TrackType.RETROFITTED
        ]

        # Initialize attributes that will be set in initialize()
        self.track_capacity: Any = None
        self.workshop_capacity: Any = None
        self.train_arrival_coordinator: Any = None
        self.wagon_pickup_coordinator: Any = None
        self.workshop_processing_coordinator: Any = None
        self.wagons_ready_for_stations: dict[str, Any] = {}
        self.wagons_completed: dict[str, Any] = {}
        self.retrofitted_wagons_ready: Any = None
        self.train_processed_event: Any = None
        self.metrics: Any = None
        self.infrastructure: Any = None

        # Validate domain requirements
        domain_validator = ScenarioDomainValidator()
        domain_result = domain_validator.validate_workshop_requirements(scenario)
        if not domain_result.is_valid:
            error_messages = [
                str(issue)
                for issue in domain_result.issues
                if issue.level.value == "ERROR"
            ]
            raise ValueError(f"Domain validation failed: {'\n'.join(error_messages)}")

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize with simulation session."""
        self.session = simulation_session
        engine = simulation_session.engine
        self.sim = engine

        # Initialize shunting operations context
        self._shunting_operations.initialize(simulation_session)

        # Initialize infrastructure using engine port

        # Use injected yard context or create new one
        if self._yard_context_injected:
            self._yard_operations = self._yard_context_injected
        else:
            # Fallback: create yard context (for backward compatibility)
            self.track_capacity = TrackCapacityManager(
                self.scenario.tracks or [],  # type: ignore[arg-type]
                self.scenario.topology,
                collection_strategy=self.scenario.track_selection_strategy,
                retrofit_strategy=self.scenario.retrofit_selection_strategy,
            )

            self.workshop_capacity = WorkshopCapacityManager(engine, self.workshops)

            yard_config = YardOperationsConfig(
                track_capacity=self.track_capacity,
                wagon_state=self.wagon_state,
                wagon_selector=self.wagon_selector,
                workshop_capacity=self.workshop_capacity,
                parking_tracks=self.parking_tracks,
            )
            self._yard_operations = YardOperationsContext(yard_config)

        # Set track_capacity and workshop_capacity from yard context
        self.track_capacity = self._yard_operations.config.track_capacity
        self.workshop_capacity = self._yard_operations.config.workshop_capacity

        # Initialize PopUp Retrofit Context
        self._popup_retrofit = PopUpRetrofitContext()
        self._popup_retrofit.initialize_station_service(engine)  # type: ignore[arg-type]

        # Create PopUp workshops
        for workshop in self.workshops:
            popup_workshop = self._popup_retrofit.create_workshop(
                workshop_id=f"popup_{workshop.track}",
                location=workshop.track,
                num_bays=workshop.retrofit_stations,
            )
            # Set event callback for retrofit events
            popup_workshop.set_event_callback(
                lambda event: self.metrics.record_event(event) if self.metrics else None
            )
            self._popup_retrofit.start_workshop_operations(popup_workshop.workshop_id)

        # Initialize coordinators
        self.train_arrival_coordinator = TrainArrivalCoordinator(self)
        self.wagon_pickup_coordinator = WagonPickupCoordinator(self)
        self.workshop_processing_coordinator = WorkshopProcessingCoordinator(self)

        # Create stores for wagon flow coordination
        self.retrofitted_wagons_ready = engine.create_store()
        self.train_processed_event = engine.create_event()

        # Initialize metrics
        self.metrics = SimulationMetrics()
        self.metrics.register(WagonCollector())
        self.metrics.register(LocomotiveCollector())
        self.metrics.register(WagonMovementCollector())

        for workshop in self.workshops:
            workshop_track_id = workshop.track
            self.wagons_ready_for_stations[workshop_track_id] = engine.create_store()
            self.wagons_completed[workshop_track_id] = engine.create_store()

    def start_processes(self) -> None:
        """Start workshop simulation processes."""
        if self.session is None:
            raise RuntimeError("Context not initialized")
        engine = self.session.engine

        logger.info("🚀 CONTEXT: Starting workshop operation processes")
        engine.schedule_process(self.train_arrival_coordinator.process_train_arrivals)
        logger.debug("  ✓ Scheduled: train_arrival_coordinator.process_train_arrivals")

        engine.schedule_process(self.wagon_pickup_coordinator.pickup_wagons_to_retrofit)
        logger.debug(
            "  ✓ Scheduled: wagon_pickup_coordinator.pickup_wagons_to_retrofit"
        )

        engine.schedule_process(
            self.workshop_processing_coordinator.move_wagons_to_stations
        )
        logger.debug(
            "  ✓ Scheduled: workshop_processing_coordinator.move_wagons_to_stations"
        )

        engine.schedule_process(_pickup_retrofitted_wagons(self))  # type: ignore[arg-type]
        logger.debug("  ✓ Scheduled: _pickup_retrofitted_wagons")

        parking_coordinator = ParkingSimPyCoordinator(self)
        engine.schedule_process(parking_coordinator.move_to_parking_simpy)
        logger.debug("  ✓ Scheduled: parking_coordinator.move_to_parking_simpy")

        # Start shunting operations
        self._shunting_operations.start_processes()

        logger.info("✅ CONTEXT: All workshop processes scheduled")

    def get_metrics(self) -> dict[str, Any]:
        """Get workshop metrics including shunting metrics."""
        workshop_metrics = dict(self.metrics.get_results()) if self.metrics else {}
        shunting_metrics = self._shunting_operations.get_metrics()

        return {
            "workshop": workshop_metrics,
            "shunting": shunting_metrics,
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._shunting_operations.cleanup()

    # Compatibility methods for existing coordinators
    @property
    def popup_retrofit(self) -> PopUpRetrofitContext:
        """PopUp retrofit context."""
        if not hasattr(self, "_popup_retrofit"):
            raise RuntimeError("Context not initialized")
        return self._popup_retrofit

    @popup_retrofit.setter
    def popup_retrofit(self, value: PopUpRetrofitContext) -> None:
        """Set PopUp retrofit context."""
        self._popup_retrofit = value

    @property
    def yard_operations(self) -> YardOperationsContext:
        """Yard operations context."""
        if not hasattr(self, "_yard_operations"):
            raise RuntimeError("Context not initialized")
        return self._yard_operations

    @yard_operations.setter
    def yard_operations(self, value: YardOperationsContext) -> None:
        """Set yard operations context."""
        self._yard_operations = value

    @property
    def shunting_operations(self) -> ShuntingOperationsContext:
        """Shunting operations context."""
        return self._shunting_operations

    @property
    def locomotive_service(self) -> Any:
        """Get locomotive service from shunting context (backward compatibility)."""
        return self._shunting_operations.get_locomotive_service()

    @property
    def locomotives(self) -> Any:
        """Get locomotives resource pool from shunting context (backward compatibility)."""
        return self._shunting_operations.locomotives

    @property
    def locomotives_collection(self) -> list[Any]:
        """Get locomotives collection from shunting context (backward compatibility)."""
        return self._shunting_operations.locomotives

    def put_wagon_for_station(
        self, workshop_track_id: str, retrofit_track_id: str, wagon: Wagon
    ) -> Generator[Any, Any, bool]:
        """Put wagon for station processing."""
        yield self.wagons_ready_for_stations[workshop_track_id].put(
            (retrofit_track_id, [wagon])
        )
        return True

    def put_completed_wagon(
        self, workshop_track_id: str, wagon: Wagon
    ) -> Generator[Any, Any, bool]:
        """Put completed wagon."""
        yield self.wagons_completed[workshop_track_id].put(wagon)
        return True

    def put_wagon_if_fits_retrofitted(self, wagon: Wagon) -> Generator[Any, Any, bool]:
        """Put wagon in retrofitted store if capacity available."""
        retrofitted_track_id = self.retrofitted_tracks[0].id
        if self.track_capacity.can_add_wagon(retrofitted_track_id, wagon.length):
            yield self.retrofitted_wagons_ready.put(wagon)
            return True
        return False

    def get_wagon_from_retrofitted(self) -> Generator[Any, Any, Wagon]:
        """Get wagon from retrofitted store."""
        wagon: Wagon = yield self.retrofitted_wagons_ready.get()
        return wagon

    def publish_wagon_location_event(
        self, wagon_id: str, from_location: str | None, to_location: str, context: str
    ) -> None:
        """Publish wagon location change event."""
        if self.metrics:
            event = WagonLocationChangedEvent.create(
                wagon_id=wagon_id,
                from_location=from_location,
                to_location=to_location,
                timestamp=Timestamp.from_simulation_time(self.sim.current_time()),
                context=context,
            )
            self.metrics.record_event(event)


def _pickup_retrofitted_wagons(
    context: WorkshopOperationsContext,
) -> Generator[Any, Any]:
    """Pickup retrofitted wagons in batches."""
    logger.info("📦 PICKUP: Starting retrofitted wagon pickup process")
    for track_id in context.wagons_completed:
        logger.debug("  ✓ Scheduling pickup for track %s", track_id)
        # Call generator directly - no lambda needed
        context.sim.schedule_process(_pickup_track_batches(context, track_id))
    yield context.sim.delay(0)
    logger.debug("✅ PICKUP: All track pickup processes scheduled")


def _pickup_track_batches(
    context: WorkshopOperationsContext, workshop_track_id: str
) -> Generator[Any, Any, Any]:  # pylint: disable=too-many-locals  # noqa: C901
    """Pickup batches from a single workshop track."""
    logger.info(
        "🔄 PICKUP: Starting batch pickup loop for track %s at t=%.1f",
        workshop_track_id,
        context.sim.current_time(),
    )
    retrofitted_track = context.retrofitted_tracks[0]
    process_times = context.scenario.process_times
    if not process_times:
        raise ValueError("Process times must be configured")
    workshop = context.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        batch: list[Wagon] = []
        logger.debug(
            "⏳ PICKUP: Waiting for completed wagon at track %s (t=%.1f)",
            workshop_track_id,
            context.sim.current_time(),
        )
        wagon: Wagon = yield context.wagons_completed[workshop_track_id].get()
        logger.info(
            "📥 PICKUP: Received completed wagon %s from track %s (t=%.1f)",
            wagon.id,
            workshop_track_id,
            context.sim.current_time(),
        )
        batch.append(wagon)

        for _ in range(batch_size - 1):
            if len(context.wagons_completed[workshop_track_id].items) > 0:
                additional_wagon: Wagon = yield context.wagons_completed[
                    workshop_track_id
                ].get()
                batch.append(additional_wagon)
            else:
                break

        loco = yield from context.locomotive_service.allocate(context)
        try:
            from_track = loco.track
            yield from context.locomotive_service.move(
                context, loco, from_track, workshop_track_id
            )

            for i, wagon in enumerate(batch):
                coupling_time = process_times.get_coupling_ticks(
                    wagon.coupler_type.value
                )
                yield context.sim.delay(coupling_time)
                if i < len(batch) - 1:
                    yield context.sim.delay(process_times.wagon_move_to_next_station)

            for wagon in batch:
                context.track_capacity.remove_wagon(workshop_track_id, wagon.length)
                context.wagon_state.start_movement(
                    wagon, workshop_track_id, retrofitted_track.id
                )

            yield from context.locomotive_service.move(
                context, loco, loco.track, retrofitted_track.id
            )
            coupler_type = (
                CouplerType.DAC
                if any(w.coupler_type == CouplerType.DAC for w in batch)
                else CouplerType.SCREW
            )
            yield from context.locomotive_service.decouple_wagons(
                context, loco, len(batch), coupler_type
            )

            arrival_time = context.sim.current_time()
            for wagon in batch:
                context.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
                context.wagon_state.complete_arrival(
                    wagon, retrofitted_track.id, WagonStatus.RETROFITTED
                )
                event = WagonArrivedEvent.create(
                    timestamp=Timestamp.from_simulation_time(arrival_time),
                    wagon_id=wagon.id,
                    track_id=retrofitted_track.id,
                    wagon_status=WagonStatus.RETROFITTED.value,
                )
                context.metrics.record_event(event)

            parking_track_id = context.parking_tracks[0].id
            yield from context.locomotive_service.move(
                context, loco, loco.track, parking_track_id
            )
            yield from context.locomotive_service.release(context, loco)

            for wagon in batch:
                yield from context.put_wagon_if_fits_retrofitted(wagon)
        except (RuntimeError, ValueError, KeyError):
            yield from context.locomotive_service.release(context, loco)
            raise
