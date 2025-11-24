"""PopUp-Sim simulation orchestrator."""

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import Any

from analytics.collectors import SimulationMetrics
from analytics.collectors import WagonCollector
from domain.locomotive_operations import LocomotiveStateManager
from domain.wagon_operations import WagonSelector
from domain.wagon_operations import WagonStateManager
from domain.workshop_operations import WorkshopDistributor
from models.locomotive import Locomotive
from models.scenario import LocoDeliveryStrategy
from models.scenario import Scenario
from models.track import TrackType
from models.train import Train
from models.wagon import CouplerType
from models.wagon import Wagon
from models.wagon import WagonStatus
from models.workshop import Workshop

from .jobs import TransportJob
from .jobs import execute_transport_job
from .resource_pool import ResourcePool
from .route_finder import find_route
from .services import DefaultLocomotiveService
from .services import LocomotiveService
from .sim_adapter import SimulationAdapter
from .track_capacity import TrackCapacityManager
from .workshop_capacity import WorkshopCapacityManager

logger = logging.getLogger(__name__)


class PopupSim:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
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
        self.name: str = 'PopupSim'
        self.sim: SimulationAdapter = sim
        self.scenario: Scenario = scenario
        self.locomotive_service = locomotive_service or DefaultLocomotiveService()

        self.locomotives_queue: list[Locomotive] = scenario.locomotives or []
        for loco in self.locomotives_queue:
            loco.record_status_change(0.0, loco.status)

        self.trains_queue: list[Train] = scenario.trains or []
        self.wagons_queue: list[Wagon] = []
        self.rejected_wagons_queue: list[Wagon] = []
        self.workshops_queue: list[Workshop] = scenario.workshops or []

        self.locomotives = ResourcePool(self.sim, self.locomotives_queue, 'Locomotives')

        self.track_capacity = TrackCapacityManager(
            scenario.tracks or [],
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

        # Create stores for wagon flow coordination
        self.wagons_ready_for_stations: dict[str, Any] = {}
        self.wagons_completed: dict[str, Any] = {}
        self.train_processed_event = sim.create_event()

        self.metrics = SimulationMetrics()
        self.metrics.register(WagonCollector())
        for workshop in self.workshops_queue:
            workshop_track_id = workshop.track_id
            self.wagons_ready_for_stations[workshop_track_id] = sim.create_store(capacity=1000)
            self.wagons_completed[workshop_track_id] = sim.create_store(capacity=1000)

        self.parking_tracks = [t for t in (scenario.tracks or []) if t.type == TrackType.PARKING]
        self.retrofitted_tracks = [t for t in (scenario.tracks or []) if t.type == TrackType.RETROFITTED]

        logger.info('Initialized %s with scenario: %s', self.name, self.scenario.scenario_id)

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

        self.sim.run_process(process_train_arrivals, self)
        self.sim.run_process(pickup_wagons_to_retrofit, self)
        self.sim.run_process(move_wagons_to_stations, self)
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


# Main simulation orchestrator - delegates to coordinators
def process_train_arrivals(popupsim: PopupSim) -> Generator[Any]:
    """Simulate train arrivals.

    This function generates train arrivals based on the provided scenario.
    It yields train arrivals as Train objects.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    scenario = popupsim.scenario
    process_times = scenario.process_times
    if not process_times:
        raise ValueError('Scenario must have process_times configured')
    if not scenario.trains:
        raise ValueError('Scenario must have trains configured')
    logger.info('Starting train arrival generator for scenario %s', scenario.scenario_id)

    for train in scenario.trains:
        logger.debug('Waiting for next train arrival at %s', train.arrival_time)
        yield popupsim.sim.delay((train.arrival_time - scenario.start_date).total_seconds() / 60.0)
        logger.info('Train %s arrived at %s', train.train_id, train.arrival_time)

        # Delay from train arrival to first wagon at hump
        yield popupsim.sim.delay(process_times.train_to_hump_delay)

        # Process wagons one by one through hump
        for wagon in train.wagons:
            wagon.status = WagonStatus.SELECTING
            logger.debug('The wagon %s was selected', wagon.wagon_id)

            if popupsim.wagon_selector.needs_retrofit(wagon):
                collection_track_id = popupsim.track_capacity.select_collection_track(wagon.length)

                if collection_track_id:
                    popupsim.track_capacity.add_wagon(collection_track_id, wagon.length)
                    popupsim.wagon_state.select_for_retrofit(wagon, collection_track_id)
                    logger.debug('Adding wagon %s to collection track %s', wagon.wagon_id, collection_track_id)
                    popupsim.wagons_queue.append(wagon)
                else:
                    popupsim.wagon_state.reject_wagon(wagon)
                    popupsim.rejected_wagons_queue.append(wagon)
                    logger.debug('Wagon %s rejected - no collection track capacity', wagon.wagon_id)
            else:
                popupsim.wagon_state.reject_wagon(wagon)
                popupsim.rejected_wagons_queue.append(wagon)

            # Delay between wagons at hump
            yield popupsim.sim.delay(process_times.wagon_hump_interval)

        # Signal that train is fully processed
        logger.info('Train %s fully processed, signaling pickup', train.train_id)
        popupsim.train_processed_event.succeed()
        # Create new event for next train
        popupsim.train_processed_event = popupsim.sim.create_event()


def _wait_for_wagons_ready(
    popupsim: PopupSim,
) -> Generator[Any, Any, tuple[str, list[Wagon]]]:  # type: ignore[misc]
    """Wait for wagons ready on collection track.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.

    Returns
    -------
    tuple[str, list[Wagon]]
        Collection track ID and list of wagons ready for pickup.

    Yields
    ------
    Any
        SimPy events while waiting for train processing.
    """
    while True:
        yield popupsim.train_processed_event.wait()

        wagons_by_track = popupsim.wagon_selector.filter_selected_wagons(popupsim.wagons_queue)
        if wagons_by_track:
            collection_track_id = next(iter(wagons_by_track))
            return (collection_track_id, wagons_by_track[collection_track_id])


def _pickup_and_couple_wagons(
    popupsim: PopupSim, loco: Locomotive, collection_track_id: str, collection_wagons: list[Wagon]
) -> Generator[list[tuple[Wagon, str]]]:  # type: ignore[misc]
    """Travel to collection, find and couple wagons.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.
    loco : Locomotive
        The locomotive to use for pickup.
    collection_track_id : str
        ID of the collection track to travel to.
    collection_wagons : list[Wagon]
        List of wagons available on the collection track.

    Returns
    -------
    list[tuple[Wagon, str]]
        List of (wagon, retrofit_track_id) tuples for wagons to pickup.

    Yields
    ------
    Any
        SimPy events for locomotive movement and coupling operations.
    """
    logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, loco.track_id, collection_track_id)
    yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, collection_track_id)
    wagons_to_pickup = _find_wagons_for_retrofit(popupsim, collection_wagons)
    if wagons_to_pickup:
        logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons_to_pickup))
        yield from popupsim.locomotive_service.couple_wagons(
            popupsim, loco, len(wagons_to_pickup), wagons_to_pickup[0][0].coupler_type
        )
    return wagons_to_pickup


def _deliver_to_retrofit_tracks(
    popupsim: PopupSim, loco: Locomotive, collection_track_id: str, wagons_by_retrofit: dict[str, list[Wagon]]
) -> Generator:
    """Deliver wagons to retrofit tracks and decouple.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.
    loco : Locomotive
        The locomotive carrying the wagons.
    collection_track_id : str
        ID of the collection track wagons are coming from.
    wagons_by_retrofit : dict[str, list[Wagon]]
        Dictionary mapping retrofit track IDs to lists of wagons to deliver.

    Yields
    ------
    Any
        SimPy events for locomotive movement and decoupling operations.
    """
    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        for wagon in retrofit_wagons:
            popupsim.track_capacity.remove_wagon(collection_track_id, wagon.length)
            popupsim.wagon_state.start_movement(wagon, collection_track_id, retrofit_track_id)

        logger.info(
            '🚂 ROUTE: Loco %s traveling [%s → %s] with %d wagons',
            loco.locomotive_id,
            loco.track_id,
            retrofit_track_id,
            len(retrofit_wagons),
        )
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, retrofit_track_id)

        for wagon in retrofit_wagons:
            popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
            popupsim.wagon_state.complete_arrival(wagon, retrofit_track_id, WagonStatus.MOVING)

        logger.debug('Loco %s decoupling %d wagons', loco.locomotive_id, len(retrofit_wagons))
        yield from popupsim.locomotive_service.decouple_wagons(popupsim, loco, len(retrofit_wagons))


def _distribute_wagons_to_workshops(popupsim: PopupSim, retrofit_track_id: str, wagons: list[Wagon]) -> Generator:
    """Distribute wagons to workshops based on available capacity.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.
    retrofit_track_id : str
        ID of the retrofit track wagons are coming from.
    wagons : list[Wagon]
        List of wagons to distribute to workshops.

    Yields
    ------
    Any
        SimPy events for putting wagons into workshop queues.
    """
    capacity_claims = {w.track_id: 0 for w in popupsim.workshops_queue}
    remaining = list(wagons)
    batch_num = 1
    current_time = popupsim.sim.current_time()

    while remaining:
        best_workshop = max(
            popupsim.workshops_queue,
            key=lambda w: popupsim.workshop_capacity.get_available_stations(w.track_id) - capacity_claims[w.track_id],
        )

        available = (
            popupsim.workshop_capacity.get_available_stations(best_workshop.track_id)
            - capacity_claims[best_workshop.track_id]
        )
        if available <= 0:
            best_workshop = popupsim.workshops_queue[0]
            batch = remaining
            remaining = []
        else:
            batch_size = min(available, len(remaining))
            batch = remaining[:batch_size]
            remaining = remaining[batch_size:]
            capacity_claims[best_workshop.track_id] += batch_size

        wagon_ids = ', '.join([w.wagon_id for w in batch])
        logger.info(
            '📦 BATCH %d: [%s] → %s (capacity: %d/%d)',
            batch_num,
            wagon_ids,
            best_workshop.track_id,
            capacity_claims[best_workshop.track_id],
            popupsim.workshop_capacity.get_available_stations(best_workshop.track_id),
        )
        batch_num += 1

        for wagon in batch:
            popupsim.wagon_state.mark_on_retrofit_track(wagon)
            popupsim.metrics.record_event('wagon_delivered', {'wagon_id': wagon.wagon_id, 'time': current_time})
            yield popupsim.wagons_ready_for_stations[best_workshop.track_id].put((retrofit_track_id, [wagon]))


def _return_loco_and_signal(
    popupsim: PopupSim, loco: Locomotive, wagons_by_retrofit: dict[str, list[Wagon]]
) -> Generator:
    """Return loco to parking and signal wagons ready."""
    logger.debug('Loco %s returning to parking', loco.locomotive_id)
    yield from _return_loco_to_parking_and_release(popupsim, loco)

    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        yield from _distribute_wagons_to_workshops(popupsim, retrofit_track_id, retrofit_wagons)


def pickup_wagons_to_retrofit(popupsim: PopupSim) -> Generator[Any]:
    """Pickup wagons from collection and move to retrofit.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.

    Yields
    ------
    Any
        SimPy events for the entire pickup and delivery process.

    Raises
    ------
    ValueError
        If scenario is missing required configuration (process_times, trains, routes).
    """
    if not popupsim.scenario.process_times:
        raise ValueError('Scenario must have process_times configured')
    if not popupsim.scenario.trains:
        raise ValueError('Scenario must have trains configured')
    if not popupsim.scenario.routes:
        raise ValueError('Scenario must have routes configured')
    logger.info('Starting wagon pickup process')
    while True:
        collection_track_id, collection_wagons = yield from _wait_for_wagons_ready(popupsim)
        loco = yield from popupsim.locomotive_service.allocate(popupsim)
        wagons_to_pickup = yield from _pickup_and_couple_wagons(popupsim, loco, collection_track_id, collection_wagons)
        if not wagons_to_pickup:
            yield from popupsim.locomotive_service.release(popupsim, loco)
            yield popupsim.sim.delay(1.0)
            continue
        wagons_by_retrofit = _group_wagons_by_retrofit_track(wagons_to_pickup)
        yield from _deliver_to_retrofit_tracks(popupsim, loco, collection_track_id, wagons_by_retrofit)
        yield from _return_loco_and_signal(popupsim, loco, wagons_by_retrofit)


def move_wagons_to_stations(popupsim: PopupSim) -> Generator[Any]:
    """Move wagon batches from retrofit track to stations.

    Blocks until batch delivered, travels via route, decouples sequentially,
    then spawns independent process for each wagon.
    """
    scenario = popupsim.scenario
    if not scenario.routes:
        raise ValueError('Scenario must have routes configured')

    logger.info('Starting wagon-to-station movement process')

    # Process each track independently
    for track_id in popupsim.wagons_ready_for_stations:
        popupsim.sim.run_process(_process_track_batches, popupsim, track_id)


def _collect_wagon_batch(
    popupsim: PopupSim, workshop_track_id: str, batch_size: int
) -> Generator[tuple[list[Wagon], str | None]]:  # type: ignore[misc]
    """Collect wagon batch up to batch_size, handling partial batches."""
    batch_wagons = []
    retrofit_track_id = None

    for i in range(batch_size):
        if i > 0 and len(popupsim.wagons_ready_for_stations[workshop_track_id].items) == 0:
            break

        item = yield popupsim.wagons_ready_for_stations[workshop_track_id].get()
        track_id, wagons = item
        if retrofit_track_id is None:
            retrofit_track_id = track_id
        batch_wagons.extend(wagons)

    return batch_wagons, retrofit_track_id


def _wait_for_workshop_ready(popupsim: PopupSim, workshop_track_id: str, workshop: Workshop) -> Generator:
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
    popupsim: PopupSim, loco: Locomotive, batch: list[Wagon], retrofit_track_id: str, workshop_id: str
) -> Generator:
    """Move loco with batch from retrofit track to workshop."""
    if popupsim.scenario.loco_delivery_strategy == LocoDeliveryStrategy.RETURN_TO_PARKING:
        logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, loco.track_id, retrofit_track_id)
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, retrofit_track_id)

    route = find_route(popupsim.scenario.routes, retrofit_track_id, workshop_id)
    if route and route.duration:
        logger.info(
            '🚂 ROUTE: Loco %s with %d wagons traveling [%s → %s] (duration: %.1f min)',
            loco.locomotive_id,
            len(batch),
            retrofit_track_id,
            workshop_id,
            route.duration,
        )
        # Wagon state tracking would go here
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, workshop_id)
    else:
        logger.warning('⚠️  No route found from %s to %s', retrofit_track_id, workshop_id)


def _decouple_and_process_wagons(popupsim: PopupSim, batch: list[Wagon], workshop_track_id: str) -> Generator:
    """Sequentially decouple wagons and spawn processing for each."""
    process_times = popupsim.scenario.process_times
    for i, wagon in enumerate(batch):
        yield popupsim.sim.delay(process_times.wagon_decoupling_time)
        logger.info('✓ Wagon %s decoupled at station (t=%.1f)', wagon.wagon_id, popupsim.sim.current_time())
        popupsim.sim.run_process(process_single_wagon, popupsim, wagon, workshop_track_id)

        if i < len(batch) - 1:
            yield popupsim.sim.delay(process_times.wagon_move_to_next_station)
            logger.info('🚂 Loco moved remaining wagons to next station')


def _return_loco_to_parking(popupsim: PopupSim, loco: Locomotive) -> Generator:
    """Return locomotive to parking based on delivery strategy."""
    if popupsim.scenario.loco_delivery_strategy == LocoDeliveryStrategy.RETURN_TO_PARKING:
        parking_track_id = popupsim.parking_tracks[0].id
        logger.info('🚂 ROUTE: Loco %s returning [%s → %s]', loco.locomotive_id, loco.track_id, parking_track_id)
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, parking_track_id)
        if popupsim.scenario.process_times.loco_parking_delay > 0:
            yield popupsim.sim.delay(popupsim.scenario.process_times.loco_parking_delay)


def _process_track_batches(popupsim: PopupSim, workshop_track_id: str) -> Generator[Any]:
    """Process wagon batches for a single workshop track."""
    workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        batch_wagons, retrofit_track_id = yield from _collect_wagon_batch(popupsim, workshop_track_id, batch_size)

        if not batch_wagons or retrofit_track_id is None:
            continue

        yield from _wait_for_workshop_ready(popupsim, workshop_track_id, workshop)

        loco = yield from popupsim.locomotive_service.allocate(popupsim)
        yield from _deliver_batch_to_workshop(popupsim, loco, batch_wagons, retrofit_track_id, workshop.workshop_id)
        yield from _decouple_and_process_wagons(popupsim, batch_wagons, workshop_track_id)
        yield from _return_loco_to_parking(popupsim, loco)
        yield from popupsim.locomotive_service.release(popupsim, loco)


def process_single_wagon(popupsim: PopupSim, wagon: Wagon, track_id: str) -> Generator[Any]:
    """Process single wagon at workshop station using SimPy Resource.

    Blocks until station available, processes wagon, then signals completion.
    """
    workshop_resource = popupsim.workshop_capacity.get_resource(track_id)
    process_times = popupsim.scenario.process_times

    # Request station (blocks until available)
    with workshop_resource.request() as station_req:
        yield station_req

        # Station acquired
        current_time = popupsim.sim.current_time()
        wagon.status = WagonStatus.RETROFITTING
        wagon.retrofit_start_time = current_time
        popupsim.workshop_capacity.record_station_occupied(track_id, wagon.wagon_id, current_time)
        logger.debug('Wagon %s started retrofit at station (t=%.1f)', wagon.wagon_id, current_time)

        # Perform retrofit work
        yield popupsim.sim.delay(process_times.wagon_retrofit_time)

        # Retrofit complete
        current_time = popupsim.sim.current_time()
        wagon.status = WagonStatus.RETROFITTED
        wagon.retrofit_end_time = current_time
        wagon.needs_retrofit = False
        wagon.coupler_type = CouplerType.DAC
        popupsim.workshop_capacity.record_station_released(track_id, current_time)
        popupsim.metrics.record_event('wagon_retrofitted', {'wagon_id': wagon.wagon_id, 'time': current_time})
        logger.info(
            'Wagon %s retrofit completed at t=%s, coupler changed to DAC', wagon.wagon_id, wagon.retrofit_end_time
        )

        # Signal completion
        yield popupsim.wagons_completed[track_id].put(wagon)
    # Station automatically released


def pickup_retrofitted_wagons(popupsim: PopupSim) -> Generator[Any]:
    """Pickup retrofitted wagons in batches.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.

    Yields
    ------
    Any
        SimPy events for spawning pickup processes for each track.
    """
    logger.info('Starting retrofitted wagon pickup process')

    # Process each track independently
    for track_id in popupsim.wagons_completed:
        popupsim.sim.run_process(_pickup_track_batches, popupsim, track_id)


def _pickup_track_batches(popupsim: PopupSim, workshop_track_id: str) -> Generator[Any]:
    """Pickup batches from a single workshop track."""
    retrofitted_track = popupsim.retrofitted_tracks[0]
    process_times = popupsim.scenario.process_times
    workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
    batch_size = workshop.retrofit_stations

    while True:
        # Collect full batch (blocks until all ready)
        batch = []
        for _ in range(batch_size):
            wagon = yield popupsim.wagons_completed[workshop_track_id].get()
            batch.append(wagon)

        logger.info('Full batch of %d wagons ready for pickup', len(batch))

        # Get locomotive
        loco = yield from popupsim.locomotive_service.allocate(popupsim)
        from_track = loco.track_id
        logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, from_track, workshop_track_id)
        yield from popupsim.locomotive_service.move(popupsim, loco, from_track, workshop_track_id)

        # Sequential coupling
        for i, wagon in enumerate(batch):
            coupling_time = (
                process_times.wagon_coupling_retrofitted_time
                if wagon.coupler_type == CouplerType.DAC
                else process_times.wagon_coupling_time
            )
            yield popupsim.sim.delay(coupling_time)
            logger.info(
                '✓ Wagon %s coupled (%s) (t=%.1f)',
                wagon.wagon_id,
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
            loco.locomotive_id,
            workshop_track_id,
            retrofitted_track.id,
            len(batch),
        )
        yield from popupsim.locomotive_service.move(popupsim, loco, loco.track_id, retrofitted_track.id)
        yield from popupsim.locomotive_service.decouple_wagons(popupsim, loco, len(batch))

        # Add to retrofitted track and update wagon states
        for wagon in batch:
            popupsim.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
            popupsim.wagon_state.complete_arrival(wagon, retrofitted_track.id, WagonStatus.RETROFITTED)
            logger.info('Wagon %s moved to retrofitted track', wagon.wagon_id)

        # Return loco to parking
        yield from _return_loco_to_parking_and_release(popupsim, loco)


def move_to_parking(popupsim: PopupSim) -> Generator[Any]:
    """Move wagons from retrofitted track to parking tracks (sequential fill).

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    yield popupsim.sim.delay(60.0)  # Wait for first wagons to reach retrofitted track
    logger.info('Starting move to parking process')

    retrofitted_track = popupsim.retrofitted_tracks[0]
    parking_tracks = popupsim.parking_tracks
    current_parking_index = 0

    while True:
        # Find wagons on retrofitted track
        wagons_on_retrofitted = [
            w
            for w in popupsim.wagons_queue
            if w.track_id == retrofitted_track.id and w.status == WagonStatus.RETROFITTED
        ]

        if not wagons_on_retrofitted:
            yield popupsim.sim.delay(1.0)
            continue

        # Select parking track (sequential fill strategy)
        parking_track = None
        for i in range(len(parking_tracks)):
            idx = (current_parking_index + i) % len(parking_tracks)
            track = parking_tracks[idx]
            if any(popupsim.track_capacity.can_add_wagon(track.id, w.length) for w in wagons_on_retrofitted):
                parking_track = track
                current_parking_index = idx
                break

        if not parking_track:
            yield popupsim.sim.delay(1.0)
            continue

        # Batch all wagons that fit on selected parking track
        wagons_to_move = [
            w for w in wagons_on_retrofitted if popupsim.track_capacity.can_add_wagon(parking_track.id, w.length)
        ]

        if not wagons_to_move:
            current_parking_index = (current_parking_index + 1) % len(parking_tracks)
            yield popupsim.sim.delay(1.0)
            continue

        # Execute transport job
        job = TransportJob(
            wagons=wagons_to_move,
            from_track=retrofitted_track.id,
            to_track=parking_track.id,
        )
        yield from execute_transport_job(popupsim, job, popupsim.locomotive_service)

        # Update final wagon status
        for wagon in wagons_to_move:
            wagon.status = WagonStatus.PARKING
            logger.info('Wagon %s moved to parking track %s', wagon.wagon_id, parking_track.id)

        # Check if current parking track is full, move to next
        remaining_wagons = [w for w in wagons_on_retrofitted if w not in wagons_to_move]
        if remaining_wagons and not any(
            popupsim.track_capacity.can_add_wagon(parking_track.id, w.length) for w in remaining_wagons
        ):
            current_parking_index = (current_parking_index + 1) % len(parking_tracks)
            logger.debug('Parking track %s full, switching to next', parking_track.id)


def _find_wagons_for_retrofit(popupsim: PopupSim, collection_wagons: list[Wagon]) -> list[tuple[Wagon, str]]:
    """Find wagons that can be moved to retrofit tracks with available stations.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance containing simulation state.
    collection_wagons : list[Wagon]
        List of wagons available on the collection track.

    Returns
    -------
    list[tuple[Wagon, str]]
        List of (wagon, retrofit_track_id) tuples for wagons that can be moved.
    """
    wagons_to_pickup = []
    # Find retrofit tracks (not workshop tracks)
    retrofit_tracks = [t for t in popupsim.scenario.tracks if t.type == TrackType.RETROFIT]
    for wagon in collection_wagons:
        for retrofit_track in retrofit_tracks:
            retrofit_track_id = retrofit_track.id
            # Check if any workshop has capacity
            has_workshop_capacity = any(
                popupsim.workshop_capacity.get_available_stations(w.track_id) > 0 for w in popupsim.workshops_queue
            )
            if has_workshop_capacity and popupsim.track_capacity.can_add_wagon(retrofit_track_id, wagon.length):
                wagons_to_pickup.append((wagon, retrofit_track_id))
                break
    return wagons_to_pickup


def _group_wagons_by_retrofit_track(wagons_to_pickup: list[tuple[Wagon, str]]) -> dict[str, list[Wagon]]:
    """Group wagons by their destination retrofit track.

    Parameters
    ----------
    wagons_to_pickup : list[tuple[Wagon, str]]
        List of (wagon, retrofit_track_id) tuples.

    Returns
    -------
    dict[str, list[Wagon]]
        Dictionary mapping retrofit track IDs to lists of wagons.
    """
    result: dict[str, list[Wagon]] = {}
    for wagon, track_id in wagons_to_pickup:
        if track_id not in result:
            result[track_id] = []
        result[track_id].append(wagon)
    return result


def _return_loco_to_parking_and_release(popupsim: PopupSim, loco: Locomotive) -> Generator[Any]:
    """Return locomotive to parking and release it.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive to return and release.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    yield from _return_loco_to_parking(popupsim, loco)
    yield from popupsim.locomotive_service.release(popupsim, loco)
