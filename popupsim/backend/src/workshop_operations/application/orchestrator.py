"""PopUp-Sim simulation orchestrator."""
# pylint: disable=all
# ruff: noqa: C901, PLR0912, PLR0915

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import Any

from analytics.application.metrics_aggregator import SimulationMetrics
from analytics.domain.collectors.locomotive_collector import LocomotiveCollector
from analytics.domain.collectors.wagon_collector import WagonCollector
from analytics.domain.collectors.wagon_movement_collector import WagonMovementCollector
from analytics.domain.events.simulation_events import WagonArrivedEvent
from analytics.domain.events.simulation_events import WagonDeliveredEvent
from analytics.domain.value_objects.timestamp import Timestamp
from popup_retrofit.application.popup_context import PopUpRetrofitContext
from workshop_operations.application.coordinators.train_arrival_coordinator import TrainArrivalCoordinator
from workshop_operations.application.coordinators.wagon_pickup_coordinator import WagonPickupCoordinator
from workshop_operations.application.coordinators.workshop_processing_coordinator import WorkshopProcessingCoordinator
from workshop_operations.application.factories.entity_factory import EntityFactory
from workshop_operations.application.services.locomotive_service import LocomotiveService
from workshop_operations.domain.aggregates.train import Train
from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.track import TrackType
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.domain.entities.workshop import Workshop
from workshop_operations.domain.services.locomotive_operations import LocomotiveStateManager
from workshop_operations.domain.services.scenario_domain_validator import ScenarioDomainValidator
from workshop_operations.domain.services.wagon_operations import WagonSelector
from workshop_operations.domain.services.wagon_operations import WagonStateManager
from workshop_operations.domain.services.workshop_operations import WorkshopDistributor
from workshop_operations.infrastructure.resources.resource_pool import ResourcePool
from workshop_operations.infrastructure.resources.track_capacity_manager import TrackCapacityManager
from workshop_operations.infrastructure.resources.workshop_capacity_manager import WorkshopCapacityManager
from workshop_operations.infrastructure.routing.transport_job import TransportJob
from workshop_operations.infrastructure.routing.transport_job import execute_transport_job
from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter
from yard_operations.application.yard_operations_context import YardOperationsContext

from configuration.domain.models.scenario import LocoDeliveryStrategy
from configuration.domain.models.scenario import Scenario

logger = logging.getLogger(__name__)


class WorkshopOrchestrator:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """High-level simulation orchestrator for PopUp-Sim.

    Parameters
    ----------
    sim : SimulationAdapter
        Simulation backend adapter.
    scenario : Scenario
        Scenario configuration to simulate.

    Attributes
    ----------
    name : str
        Simulator name.
    sim : SimulationAdapter
        Active simulation adapter.
    scenario : Scenario
        Current scenario configuration.
    trains_queue : list[Train]
        Queue of trains from scenario.
    wagons_queue : list[Wagon]
        Queue of wagons to process.
    workshops_queue : list[Workshop]
        Queue of workshops from scenario.
    """

    def __init__(
        self, sim: SimulationAdapter, scenario: Scenario, locomotive_service: LocomotiveService | None = None
    ) -> None:
        self.name: str = 'WorkshopOrchestrator'
        self.sim: SimulationAdapter = sim
        self.scenario: Scenario = scenario
        # Use enhanced shunting locomotive service for all yard operations
        if locomotive_service is None:
            from shunting_operations.application.shunting_locomotive_service import ShuntingLocomotiveService

            locomotive_service = ShuntingLocomotiveService()
        self.locomotive_service = locomotive_service

        # Convert DTOs to entities

        self.locomotives_queue: list[Locomotive] = [
            EntityFactory.create_locomotive(dto) for dto in (scenario.locomotives or [])
        ]
        for loco in self.locomotives_queue:
            loco.record_status_change(0.0, loco.status)

        self.trains_queue: list[Train] = scenario.trains or []
        self.wagons_queue: list[Wagon] = []
        self.rejected_wagons_queue: list[Wagon] = []
        self.workshops_queue: list[Workshop] = [
            EntityFactory.create_workshop(dto) for dto in (scenario.workshops or [])
        ]

        self.locomotives = ResourcePool(self.sim, self.locomotives_queue, 'Locomotives')  # type: ignore[arg-type]

        self.track_capacity = TrackCapacityManager(
            scenario.tracks or [],  # type: ignore[arg-type]
            scenario.topology,
            collection_strategy=scenario.track_selection_strategy,
            retrofit_strategy=scenario.retrofit_selection_strategy,
        )

        # Initialize workshop capacity management
        self.workshop_capacity = WorkshopCapacityManager(sim, self.workshops_queue)

        # Initialize domain services
        self.wagon_selector = WagonSelector()
        self.wagon_state = WagonStateManager()
        self.loco_state = LocomotiveStateManager()
        self.workshop_distributor = WorkshopDistributor()

        # Extract parking and retrofitted tracks
        self.parking_tracks = [t for t in (scenario.tracks or []) if t.type == TrackType.PARKING]
        self.retrofitted_tracks = [t for t in (scenario.tracks or []) if t.type == TrackType.RETROFITTED]

        # Initialize Yard Operations Context
        from yard_operations.application.yard_operations_config import YardOperationsConfig

        yard_config = YardOperationsConfig(
            track_capacity=self.track_capacity,
            wagon_state=self.wagon_state,
            wagon_selector=self.wagon_selector,
            workshop_capacity=self.workshop_capacity,
            parking_tracks=self.parking_tracks,
        )
        self.yard_operations = YardOperationsContext(yard_config)

        # Initialize PopUp Retrofit Context
        self.popup_retrofit = PopUpRetrofitContext()
        self.popup_retrofit.initialize_station_service(sim)

        # Create PopUp workshops for each workshop in scenario
        for workshop in self.workshops_queue:
            popup_workshop = self.popup_retrofit.create_workshop(
                workshop_id=f'popup_{workshop.track}', location=workshop.track, num_bays=workshop.retrofit_stations
            )
            self.popup_retrofit.start_workshop_operations(popup_workshop.workshop_id)
            logger.info(
                'Created PopUp workshop %s with %d bays', popup_workshop.workshop_id, len(popup_workshop.retrofit_bays)
            )

        # Initialize process coordinators
        self.train_arrival_coordinator = TrainArrivalCoordinator(self)
        self.wagon_pickup_coordinator = WagonPickupCoordinator(self)
        self.workshop_processing_coordinator = WorkshopProcessingCoordinator(self)

        # Validate domain requirements
        domain_validator = ScenarioDomainValidator()
        domain_result = domain_validator.validate_workshop_requirements(scenario)
        if not domain_result.is_valid:
            error_messages = [str(issue) for issue in domain_result.issues if issue.level.value == 'ERROR']
            raise ValueError(f'Domain validation failed: {"\n".join(error_messages)}')

        # Create stores for wagon flow coordination
        self.wagons_ready_for_stations: dict[str, Any] = {}
        self.wagons_completed: dict[str, Any] = {}
        self.retrofitted_wagons_ready = sim.create_store()  # Unlimited - capacity managed by TrackCapacityManager
        self.train_processed_event = sim.create_event()

        self.metrics = SimulationMetrics()
        self.metrics.register(WagonCollector())
        # Register collectors for Gantt chart visualization
        self.metrics.register(LocomotiveCollector())
        self.metrics.register(WagonMovementCollector())
        for workshop in self.workshops_queue:
            workshop_track_id = workshop.track
            self.wagons_ready_for_stations[workshop_track_id] = (
                sim.create_store()
            )  # Unlimited - capacity managed by TrackCapacityManager
            self.wagons_completed[workshop_track_id] = (
                sim.create_store()
            )  # Unlimited - workshop stations manage capacity

        logger.info('Initialized %s with scenario: %s (domain validated)', self.name, self.scenario.id)

    def get_simtime_limit_from_scenario(self) -> float:
        """Determine simulation time limit from scenario configuration.

        Returns
        -------
        float
            Simulation time limit in minutes.
        """
        start_datetime = self.scenario.start_date
        end_datetime = self.scenario.end_date
        delta = end_datetime - start_datetime
        return delta.total_seconds() / 60.0

    def run(self, until: float | None = None) -> None:
        """Run simulation until specified time or scenario end.

        Parameters
        ----------
        until : float | None, optional
            Simulation time limit in minutes. If None, uses scenario end time.
        """
        if not until:
            until = self.get_simtime_limit_from_scenario()
        logger.info('Starting %s for: %s', self.name, self.scenario)

        self.sim.run_process(self.train_arrival_coordinator.process_train_arrivals)
        self.sim.run_process(self.wagon_pickup_coordinator.pickup_wagons_to_retrofit)
        self.sim.run_process(self.workshop_processing_coordinator.move_wagons_to_stations)
        self.sim.run_process(pickup_retrofitted_wagons, self)
        self.sim.run_process(move_to_parking, self)

        self.sim.run(until)
        logger.info('Simulation completed.')

    def get_metrics(self) -> dict[str, list[dict[str, Any]]]:
        """Get simulation metrics grouped by category.

        Returns
        -------
        dict[str, list[dict[str, Any]]]
            Metrics grouped by category.
        """
        return self.metrics.get_results()

    def put_wagon_if_fits_retrofitted(self, wagon: Wagon) -> Generator[Any, Any, bool]:
        """Put wagon in retrofitted store only if track has physical capacity.

        Parameters
        ----------
        wagon : Wagon
            Wagon to put in store.

        Returns
        -------
        bool
            True if wagon was added, False if no capacity.

        Yields
        ------
        Any
            SimPy events.
        """
        retrofitted_track_id = self.retrofitted_tracks[0].id
        if self.track_capacity.can_add_wagon(retrofitted_track_id, wagon.length):
            # Note: Physical capacity already managed by pickup process
            # This is just workflow coordination
            yield self.retrofitted_wagons_ready.put(wagon)
            return True  # type: ignore[return-value]
        logger.warning('Cannot add wagon %s to retrofitted store - track %s full', wagon.id, retrofitted_track_id)
        return False  # type: ignore[return-value]

    def get_wagon_from_retrofitted(self) -> Generator[Any, Any, Wagon]:
        """Get wagon from retrofitted store and update capacity tracking.

        Returns
        -------
        Wagon
            Wagon retrieved from store.

        Yields
        ------
        Any
            SimPy events.
        """
        wagon: Wagon = yield self.retrofitted_wagons_ready.get()
        # Note: Physical capacity will be updated by transport job
        return wagon  # type: ignore[return-value]

    def put_wagon_for_station(
        self, workshop_track_id: str, retrofit_track_id: str, wagon: Wagon
    ) -> Generator[Any, Any, bool]:
        """Put wagon in workshop station queue with capacity validation.

        Parameters
        ----------
        workshop_track_id : str
            Workshop track ID.
        retrofit_track_id : str
            Source retrofit track ID.
        wagon : Wagon
            Wagon to queue for station.

        Returns
        -------
        bool
            True if wagon was queued, False if no capacity.

        Yields
        ------
        Any
            SimPy events.
        """
        # Workshop stations manage their own capacity via SimPy Resources
        # This is just workflow coordination
        yield self.wagons_ready_for_stations[workshop_track_id].put((retrofit_track_id, [wagon]))
        return True  # type: ignore[return-value]

    def put_completed_wagon(self, workshop_track_id: str, wagon: Wagon) -> Generator[Any, Any, bool]:
        """Put completed wagon in workshop completion queue.

        Parameters
        ----------
        workshop_track_id : str
            Workshop track ID.
        wagon : Wagon
            Completed wagon.

        Returns
        -------
        bool
            True if wagon was queued.

        Yields
        ------
        Any
            SimPy events.
        """
        # Workshop completion queue - no physical capacity limits
        yield self.wagons_completed[workshop_track_id].put(wagon)
        return True  # type: ignore[return-value]


# Main simulation orchestrator - delegates to coordinators


def _deliver_to_retrofit_tracks(
    popupsim: WorkshopOrchestrator,
    _loco: Locomotive | None,
    collection_track_id: str,
    wagons_by_retrofit: dict[str, list[Wagon]],
) -> Generator:
    """Deliver wagons to retrofit tracks using transport jobs.

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance containing simulation state.
    loco : Locomotive | None
        Unused parameter (kept for compatibility).
    collection_track_id : str
        ID of the collection track wagons are coming from.
    wagons_by_retrofit : dict[str, list[Wagon]]
        Dictionary mapping retrofit track IDs to lists of wagons to deliver.

    Yields
    ------
    Any
        SimPy events for transport job execution.
    """
    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        # Use transport job for proper event emission
        job = TransportJob(
            wagons=retrofit_wagons,
            from_track=collection_track_id,
            to_track=retrofit_track_id,
        )
        yield from execute_transport_job(popupsim, job, popupsim.locomotive_service)

        # Update wagon status after transport
        for wagon in retrofit_wagons:
            wagon.status = WagonStatus.MOVING


def _distribute_wagons_to_workshops(
    popupsim: WorkshopOrchestrator, retrofit_track_id: str, wagons: list[Wagon]
) -> Generator:
    """Distribute wagons to workshops based on available capacity.

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance containing simulation state.
    retrofit_track_id : str
        ID of the retrofit track wagons are coming from.
    wagons : list[Wagon]
        List of wagons to distribute to workshops.

    Yields
    ------
    Any
        SimPy events for putting wagons into workshop queues.
    """
    capacity_claims = {w.track: 0 for w in popupsim.workshops_queue}
    remaining = list(wagons)
    batch_num = 1
    current_time = popupsim.sim.current_time()

    while remaining:
        best_workshop = max(
            popupsim.workshops_queue,
            key=lambda w: popupsim.workshop_capacity.get_available_stations(w.track) - capacity_claims[w.track],
        )

        available = (
            popupsim.workshop_capacity.get_available_stations(best_workshop.track)
            - capacity_claims[best_workshop.track]
        )
        if available <= 0:
            best_workshop = popupsim.workshops_queue[0]
            batch = remaining
            remaining = []
        else:
            batch_size = min(available, len(remaining))
            batch = remaining[:batch_size]
            remaining = remaining[batch_size:]
            capacity_claims[best_workshop.track] += batch_size

        wagon_ids = ', '.join([w.id for w in batch])
        logger.info(
            '📦 BATCH %d: [%s] → %s (capacity: %d/%d)',
            batch_num,
            wagon_ids,
            best_workshop.track,
            capacity_claims[best_workshop.track],
            popupsim.workshop_capacity.get_available_stations(best_workshop.track),
        )
        batch_num += 1

        for wagon in batch:
            popupsim.wagon_state.mark_on_retrofit_track(wagon)

            # Record domain event
            event = WagonDeliveredEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time), wagon_id=wagon.id
            )
            popupsim.metrics.record_event(event)

            yield from popupsim.put_wagon_for_station(best_workshop.track, retrofit_track_id, wagon)


def _signal_wagons_ready(popupsim: WorkshopOrchestrator, wagons_by_retrofit: dict[str, list[Wagon]]) -> Generator:
    """Signal wagons ready for workshop processing."""
    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        yield from _distribute_wagons_to_workshops(popupsim, retrofit_track_id, retrofit_wagons)


def _collect_wagon_batch(
    popupsim: WorkshopOrchestrator, workshop_track_id: str, batch_size: int
) -> Generator[Any, Any, tuple[list[Wagon], str | None]]:
    """Collect wagon batch up to batch_size, handling partial batches."""
    batch_wagons: list[Wagon] = []
    retrofit_track_id: str | None = None

    for i in range(batch_size):
        if i > 0 and len(popupsim.wagons_ready_for_stations[workshop_track_id].items) == 0:
            break

        item = yield popupsim.wagons_ready_for_stations[workshop_track_id].get()
        track_id, wagons = item
        if retrofit_track_id is None:
            retrofit_track_id = track_id
        batch_wagons.extend(wagons)

    return batch_wagons, retrofit_track_id


def _wait_for_workshop_ready(popupsim: WorkshopOrchestrator, workshop_track_id: str, workshop: Workshop) -> Generator:
    """Wait until workshop track and all stations are empty."""
    while True:
        track_empty = popupsim.track_capacity.get_available_capacity(
            workshop_track_id
        ) == popupsim.track_capacity.get_total_capacity(workshop_track_id)
        stations_empty = (
            popupsim.workshop_capacity.get_available_stations(workshop_track_id) == workshop.retrofit_stations
        )
        if track_empty and stations_empty:
            break
        yield popupsim.sim.delay(0.1)


def _deliver_batch_to_workshop(
    popupsim: WorkshopOrchestrator,
    _loco: Locomotive | None,
    batch: list[Wagon],
    retrofit_track_id: str,
    workshop_track_id: str,
) -> Generator:
    """Move loco with batch from retrofit track to workshop and start processing immediately."""
    # Allocate locomotive
    loco = yield from popupsim.locomotive_service.allocate(popupsim)

    try:
        # Move to pickup location
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track, retrofit_track_id)

        # Couple wagons
        coupler_type = batch[0].coupler_type if batch else CouplerType.SCREW
        yield from popupsim.locomotive_service.couple_wagons(popupsim, loco, len(batch), coupler_type)

        # Update wagon states - remove from source track
        for wagon in batch:
            popupsim.track_capacity.remove_wagon(retrofit_track_id, wagon.length)
            wagon.status = WagonStatus.MOVING
            wagon.source_track_id = retrofit_track_id
            wagon.destination_track_id = workshop_track_id
            wagon.track = None

        # Move to workshop
        yield from popupsim.locomotive_service.move(popupsim, loco, retrofit_track_id, workshop_track_id)

        # Decouple wagons
        yield from popupsim.locomotive_service.decouple_wagons(popupsim, loco, len(batch), coupler_type)

        # Update wagon states - add to destination track
        for wagon in batch:
            popupsim.track_capacity.add_wagon(workshop_track_id, wagon.length)
            wagon.track = workshop_track_id
            wagon.source_track_id = None
            wagon.destination_track_id = None

        # Start wagon processing immediately (before locomotive returns)
        yield from _process_wagons_at_workshop(popupsim, batch, workshop_track_id)

        # Return locomotive to parking
        parking_track_id = popupsim.parking_tracks[0].id
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track, parking_track_id)

    finally:
        # Release locomotive
        yield from popupsim.locomotive_service.release(popupsim, loco)


def _process_wagons_at_workshop(
    popupsim: WorkshopOrchestrator, batch: list[Wagon], workshop_track_id: str
) -> Generator[Any, Any]:
    """Spawn processing for each wagon at workshop."""
    for wagon in batch:
        popupsim.sim.run_process(process_single_wagon, popupsim, wagon, workshop_track_id)
    yield popupsim.sim.delay(0)  # Ensure generator yields


def _return_loco_to_parking(popupsim: WorkshopOrchestrator, loco: Locomotive) -> Generator[Any, Any]:
    """Return locomotive to parking based on delivery strategy."""
    if popupsim.scenario.loco_delivery_strategy == LocoDeliveryStrategy.RETURN_TO_PARKING:
        parking_track_id = popupsim.parking_tracks[0].id
        logger.info('🚂 ROUTE: Loco %s returning [%s → %s]', loco.id, loco.track, parking_track_id)
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track, parking_track_id)
        process_times = popupsim.scenario.process_times
        if process_times and process_times.loco_parking_delay > 0:
            yield popupsim.sim.delay(process_times.loco_parking_delay)


def _process_track_batches(popupsim: WorkshopOrchestrator, workshop_track_id: str) -> Generator[Any]:
    """Process wagon batches for a single workshop track."""
    workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        batch_wagons, retrofit_track_id = yield from _collect_wagon_batch(popupsim, workshop_track_id, batch_size)

        if not batch_wagons or retrofit_track_id is None:
            continue

        yield from _wait_for_workshop_ready(popupsim, workshop_track_id, workshop)

        # Deliver batch and start processing (processing now happens inside delivery)
        yield from _deliver_batch_to_workshop(popupsim, None, batch_wagons, retrofit_track_id, workshop.track)


def process_single_wagon(popupsim: WorkshopOrchestrator, wagon: Wagon, track_id: str) -> Generator[Any, Any]:
    """Process single wagon at PopUp workshop using PopUp Retrofit Context.

    Blocks until station available, processes wagon using PopUp facilities, then signals completion.
    """
    workshop_resource = popupsim.workshop_capacity.get_resource(track_id)
    process_times = popupsim.scenario.process_times
    if not process_times:
        raise ValueError('Process times must be configured')

    # Use PopUp Retrofit Context station service for processing
    station_service = popupsim.popup_retrofit.get_station_service()
    yield from station_service.process_wagon_at_station(
        wagon=wagon,
        workshop_resource=workshop_resource,
        track_id=track_id,
        process_time=process_times.wagon_retrofit_time,
        workshop_capacity_manager=popupsim.workshop_capacity,
        metrics=popupsim.metrics,
    )

    # Signal completion
    yield from popupsim.put_completed_wagon(track_id, wagon)


def pickup_retrofitted_wagons(popupsim: WorkshopOrchestrator) -> Generator[Any]:
    """Pickup retrofitted wagons in batches.

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance containing simulation state.

    Yields
    ------
    Any
        SimPy events for spawning pickup processes for each track.
    """
    logger.info('Starting retrofitted wagon pickup process')

    # Process each track independently
    for track_id in popupsim.wagons_completed:
        popupsim.sim.run_process(_pickup_track_batches, popupsim, track_id)


def _pickup_track_batches(popupsim: WorkshopOrchestrator, workshop_track_id: str) -> Generator[Any, Any, Any]:
    """Pickup batches from a single workshop track."""
    retrofitted_track = popupsim.retrofitted_tracks[0]
    process_times = popupsim.scenario.process_times
    if not process_times:
        raise ValueError('Process times must be configured')
    workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        # Collect batch with timeout for partial batches
        batch: list[Wagon] = []

        # Get first wagon (blocks until available)
        wagon: Wagon = yield popupsim.wagons_completed[workshop_track_id].get()
        batch.append(wagon)

        # Try to collect additional wagons up to batch_size with timeout
        for _ in range(batch_size - 1):
            if len(popupsim.wagons_completed[workshop_track_id].items) > 0:
                additional_wagon: Wagon = yield popupsim.wagons_completed[workshop_track_id].get()
                batch.append(additional_wagon)
            else:
                # No more wagons immediately available, wait briefly
                try:
                    timeout_event = popupsim.sim.delay(5.0)  # 5 minute timeout
                    get_event = popupsim.wagons_completed[workshop_track_id].get()
                    result = yield timeout_event | get_event
                    if get_event in result:
                        batch.append(result[get_event])
                    else:
                        # Timeout - proceed with partial batch
                        break
                except Exception:
                    # Timeout or other issue - proceed with partial batch
                    break

        logger.info('Batch of %d wagons ready for pickup (target: %d)', len(batch), batch_size)

        # Get locomotive
        loco: Locomotive = yield from popupsim.locomotive_service.allocate(popupsim)
        try:
            from_track = loco.track
            logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.id, from_track, workshop_track_id)
            yield from popupsim.locomotive_service.move(popupsim, loco, from_track, workshop_track_id)

            # Sequential coupling using coupler-specific times
            for i, wagon in enumerate(batch):
                coupling_time = process_times.get_coupling_time(wagon.coupler_type.value)
                yield popupsim.sim.delay(coupling_time)
                logger.info(
                    '✓ Wagon %s coupled (%s) (t=%.1f)',
                    wagon.id,
                    wagon.coupler_type.value,
                    popupsim.sim.current_time(),
                )

                if i < len(batch) - 1:
                    yield popupsim.sim.delay(process_times.wagon_move_to_next_station)
                    logger.info('🚂 Loco moved to next station')

            # Remove from workshop track and update wagon states
            for wagon in batch:
                popupsim.track_capacity.remove_wagon(workshop_track_id, wagon.length)
                popupsim.wagon_state.start_movement(wagon, workshop_track_id, retrofitted_track.id)

            # Travel to retrofitted track
            logger.info(
                '🚂 ROUTE: Loco %s traveling [%s → %s] with %d wagons',
                loco.id,
                workshop_track_id,
                retrofitted_track.id,
                len(batch),
            )
            yield from popupsim.locomotive_service.move(popupsim, loco, loco.track, retrofitted_track.id)
            # Use DAC coupler type for retrofitted wagons
            coupler_type = (
                CouplerType.DAC if any(w.coupler_type == CouplerType.DAC for w in batch) else CouplerType.SCREW
            )
            yield from popupsim.locomotive_service.decouple_wagons(popupsim, loco, len(batch), coupler_type)

            # Add to retrofitted track and update wagon states
            arrival_time = popupsim.sim.current_time()
            for wagon in batch:
                popupsim.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
                popupsim.wagon_state.complete_arrival(wagon, retrofitted_track.id, WagonStatus.RETROFITTED)
                logger.info('Wagon %s moved to retrofitted track', wagon.id)

                # Emit wagon arrived event
                event = WagonArrivedEvent.create(
                    timestamp=Timestamp.from_simulation_time(arrival_time),
                    wagon_id=wagon.id,
                    track_id=retrofitted_track.id,
                    wagon_status=WagonStatus.RETROFITTED.value,
                )
                popupsim.metrics.record_event(event)

            # Return loco to parking and release
            yield from _return_loco_to_parking_and_release(popupsim, loco)

            # Signal wagons ready for parking
            for wagon in batch:
                yield from popupsim.put_wagon_if_fits_retrofitted(wagon)
        except Exception:
            yield from popupsim.locomotive_service.release(popupsim, loco)
            raise


def move_to_parking(popupsim: WorkshopOrchestrator) -> Generator[Any]:
    """Move wagons from retrofitted track to parking tracks (sequential fill).

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    logger.info('Starting move to parking process')

    retrofitted_track = popupsim.retrofitted_tracks[0]
    wagons_batch: list[Wagon] = []

    while True:
        # Get wagon from retrofitted wagons store (blocks until available)
        wagon: Wagon = yield from popupsim.get_wagon_from_retrofitted()
        wagons_batch.append(wagon)

        # Collect additional wagons if available (non-blocking)
        while len(popupsim.retrofitted_wagons_ready.items) > 0 and len(wagons_batch) < 10:
            additional_wagon: Wagon = yield from popupsim.get_wagon_from_retrofitted()
            wagons_batch.append(additional_wagon)

        # Use parking area to select track
        parking_track = popupsim.yard_operations.parking_area.select_parking_track(wagons_batch)

        if not parking_track:
            # No parking capacity, put wagons back and wait
            for wagon in wagons_batch:
                yield from popupsim.put_wagon_if_fits_retrofitted(wagon)
            wagons_batch = []
            yield popupsim.sim.delay(1.0)
            continue

        # Use parking area to determine which wagons fit
        wagons_to_move, wagons_to_requeue = popupsim.yard_operations.parking_area.get_wagons_that_fit(
            parking_track, wagons_batch
        )

        # Put back wagons that don't fit
        for wagon in wagons_to_requeue:
            yield from popupsim.put_wagon_if_fits_retrofitted(wagon)

        wagons_batch = []

        if not wagons_to_move:
            popupsim.yard_operations.parking_area.advance_to_next_track()
            yield popupsim.sim.delay(1.0)
            continue

        # Reserve parking capacity before transport (atomic operation)
        total_length = sum(w.length for w in wagons_to_move)
        if not popupsim.track_capacity.can_add_wagon(parking_track.id, total_length):
            # Capacity changed since validation - requeue wagons
            for wagon in wagons_to_move:
                yield from popupsim.put_wagon_if_fits_retrofitted(wagon)
            popupsim.yard_operations.parking_area.advance_to_next_track()
            yield popupsim.sim.delay(1.0)
            continue

        # Execute transport job (capacity will be managed by transport job)
        job = TransportJob(
            wagons=wagons_to_move,
            from_track=retrofitted_track.id,
            to_track=parking_track.id,
        )
        yield from execute_transport_job(popupsim, job, popupsim.locomotive_service)

        # Update final wagon status
        for wagon in wagons_to_move:
            wagon.status = WagonStatus.PARKING
            logger.info('Wagon %s moved to parking track %s', wagon.id, parking_track.id)

        # Check if current parking track is full, move to next
        # Use a reasonable minimum wagon length to check if track has any remaining capacity
        min_wagon_length = 10.0  # Minimum expected wagon length
        if not popupsim.track_capacity.can_add_wagon(parking_track.id, min_wagon_length):
            popupsim.yard_operations.parking_area.advance_to_next_track()
            logger.debug('Parking track %s full, switching to next', parking_track.id)


def _return_loco_to_parking_and_release(popupsim: WorkshopOrchestrator, loco: Locomotive) -> Generator[Any]:
    """Return locomotive to parking and release it.

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance.
    loco : Locomotive
        The locomotive to return and release.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    yield from _return_loco_to_parking(popupsim, loco)
    yield from popupsim.locomotive_service.release(popupsim, loco)
