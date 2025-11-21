"""PopUp-Sim simulation orchestrator."""

from collections.abc import Generator
import logging
from typing import Any
from typing import cast

from models.locomotive import Locomotive
from models.locomotive import LocoStatus
from models.scenario import Scenario
from models.track import TrackType
from models.train import Train
from models.wagon import CouplerType
from models.wagon import Wagon
from models.wagon import WagonStatus
from models.workshop import Workshop

from .analysis.collectors.wagon_flow import WagonFlowCollector
from .analysis.metrics import SimulationMetrics
from .jobs import TransportJob
from .jobs import execute_transport_job
from .resource_pool import ResourcePool
from .route_finder import find_route
from .sim_adapter import SimulationAdapter
from .track_capacity import TrackCapacityManager
from .workshop_capacity import WorkshopCapacityManager

logger = logging.getLogger(__name__)


class PopupSim:  # pylint: disable=too-few-public-methods
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

    def __init__(self, sim: SimulationAdapter, scenario: Scenario) -> None:
        self.name: str = PopupSim
        self.sim: SimulationAdapter = sim
        self.scenario: Scenario = scenario
        if not scenario.locomotives:
            raise ValueError('Scenario must have at least one locomotive to simulate.')
        self.locomotives_queue: list[Locomotive] = scenario.locomotives
        # Initialize status history for all locomotives
        for loco in self.locomotives_queue:
            loco.record_status_change(0.0, loco.status)
        if not scenario.trains:
            raise ValueError('Scenario must have at least one train to simulate.')
        self.trains_queue: list[Train] = scenario.trains
        self.wagons_queue: list[Wagon] = []
        self.workshops_queue: list[Workshop] = scenario.workshops

        self.locomotives = ResourcePool(self.sim, self.locomotives_queue, 'Locomotives')

        # Initialize track capacity management
        if scenario.tracks and scenario.topology:
            self.track_capacity = TrackCapacityManager(
                scenario.tracks,
                scenario.topology,
                collection_strategy=scenario.track_selection_strategy,
                retrofit_strategy=scenario.retrofit_selection_strategy,
            )
        else:
            raise ValueError('Scenario must have tracks and topology for capacity management.')

        # Initialize workshop capacity management
        self.workshop_capacity = WorkshopCapacityManager(sim, self.workshops_queue)

        # Create stores for wagon flow coordination
        self.wagons_ready_for_stations: dict[str, Any] = {}
        self.wagons_completed: dict[str, Any] = {}
        self.train_processed_event = sim.create_event()

        # Initialize metrics collection
        self.metrics = SimulationMetrics()
        self.metrics.register(WagonFlowCollector())
        for workshop in self.workshops_queue:
            workshop_track_id = workshop.track_id
            self.wagons_ready_for_stations[workshop_track_id] = sim.create_store(capacity=1000)
            self.wagons_completed[workshop_track_id] = sim.create_store(capacity=1000)

        # Cache track lookups to avoid repeated list comprehensions
        if not scenario.tracks:
            raise ValueError('Scenario must have tracks configured')
        self.parking_tracks = [
            t
            for t in scenario.tracks
            if t.type == TrackType.PARKING or (hasattr(t.type, 'value') and t.type.value == 'resourceparking')
        ]
        self.retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]

        if not self.parking_tracks:
            # Try to find any track that could serve as parking
            self.parking_tracks = [t for t in scenario.tracks if 'parking' in str(t.type).lower()]

        if not self.retrofitted_tracks:
            raise ValueError('Scenario must have at least one retrofitted track')
        
        # Parking tracks are optional for testing capacity management
        if not self.parking_tracks:
            logger.warning('No parking tracks found - some simulation features may not work')

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
            if wagon.needs_retrofit and not wagon.is_loaded:
                # Select collection track using configured strategy
                collection_track_id = popupsim.track_capacity.select_collection_track(wagon.length)

                if collection_track_id:
                    popupsim.track_capacity.add_wagon(collection_track_id, wagon.length)
                    wagon.track_id = collection_track_id
                    wagon.status = WagonStatus.SELECTED
                    logger.debug('Adding wagon %s to collection track %s', wagon.wagon_id, collection_track_id)
                    popupsim.wagons_queue.append(wagon)
                else:
                    wagon.status = WagonStatus.REJECTED
                    logger.debug('Wagon %s rejected - no collection track capacity', wagon.wagon_id)
            else:
                wagon.status = WagonStatus.REJECTED

            # Delay between wagons at hump
            yield popupsim.sim.delay(process_times.wagon_hump_interval)
        
        # Signal that train is fully processed
        logger.info('Train %s fully processed, signaling pickup', train.train_id)
        popupsim.train_processed_event.trigger()


def _wait_for_wagons_ready(popupsim: PopupSim) -> Generator[tuple[str, list[Wagon]]]:  # type: ignore[misc]
    """Wait for wagons ready on collection track."""
    while True:
        yield popupsim.train_processed_event.wait()
        
        wagons_by_track: dict[str, list[Wagon]] = {}
        for wagon in popupsim.wagons_queue:
            if wagon.status == WagonStatus.SELECTED and wagon.track_id:
                wagons_by_track.setdefault(wagon.track_id, []).append(wagon)
        if wagons_by_track:
            collection_track_id = next(iter(wagons_by_track))
            return collection_track_id, wagons_by_track[collection_track_id]


def _pickup_and_couple_wagons(
    popupsim: PopupSim, loco: Locomotive, collection_track_id: str, collection_wagons: list[Wagon]
) -> Generator[list[tuple[Wagon, str]]]:  # type: ignore[misc]
    """Travel to collection, find and couple wagons."""
    logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, loco.track_id, collection_track_id)
    yield from move_locomotive(popupsim, loco, loco.track_id, collection_track_id)
    wagons_to_pickup = _find_wagons_for_retrofit(popupsim, collection_wagons)
    if wagons_to_pickup:
        logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons_to_pickup))
        yield from couple_wagons(popupsim, loco, len(wagons_to_pickup), wagons_to_pickup[0][0].coupler_type)
    return wagons_to_pickup


def _deliver_to_retrofit_tracks(
    popupsim: PopupSim, loco: Locomotive, collection_track_id: str, wagons_by_retrofit: dict[str, list[Wagon]]
) -> Generator:
    """Deliver wagons to retrofit tracks and decouple."""
    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        for wagon in retrofit_wagons:
            popupsim.track_capacity.remove_wagon(collection_track_id, wagon.length)
            wagon.status = WagonStatus.MOVING
            wagon.source_track_id = collection_track_id
            wagon.destination_track_id = retrofit_track_id
            wagon.track_id = None
        logger.info('🚂 ROUTE: Loco %s traveling [%s → %s] with %d wagons',
                   loco.locomotive_id, loco.track_id, retrofit_track_id, len(retrofit_wagons))
        yield from move_locomotive(popupsim, loco, loco.track_id, retrofit_track_id)
        for wagon in retrofit_wagons:
            popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
            wagon.track_id = retrofit_track_id
            wagon.source_track_id = None
            wagon.destination_track_id = None
            wagon.status = WagonStatus.MOVING
        logger.debug('Loco %s decoupling %d wagons', loco.locomotive_id, len(retrofit_wagons))
        yield from decouple_wagons(popupsim, loco, len(retrofit_wagons))


def _return_loco_and_signal(
    popupsim: PopupSim, loco: Locomotive, wagons_by_retrofit: dict[str, list[Wagon]]
) -> Generator:
    """Return loco to parking and signal wagons ready."""
    parking_track_id = popupsim.parking_tracks[0].id
    logger.debug('Loco %s returning to parking', loco.locomotive_id)
    yield from move_locomotive(popupsim, loco, loco.track_id, parking_track_id)
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)
    yield from release_locomotive(popupsim, loco)
    current_time = popupsim.sim.current_time()
    for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
        # Find workshop for this retrofit track (match by proximity or first available)
        workshop_track_id = popupsim.workshops_queue[0].track_id if popupsim.workshops_queue else None
        if workshop_track_id:
            for wagon in retrofit_wagons:
                wagon.status = WagonStatus.ON_RETROFIT_TRACK
                popupsim.metrics.record_event('wagon_delivered', {'wagon_id': wagon.wagon_id, 'time': current_time})
                logger.info('Wagon %s ready for station at t=%.1f', wagon.wagon_id, current_time)
                yield popupsim.wagons_ready_for_stations[workshop_track_id].put((retrofit_track_id, [wagon]))


def pickup_wagons_to_retrofit(popupsim: PopupSim) -> Generator[Any]:
    """Pickup wagons from collection and move to retrofit."""
    if not popupsim.scenario.process_times:
        raise ValueError('Scenario must have process_times configured')
    if not popupsim.scenario.trains:
        raise ValueError('Scenario must have trains configured')
    if not popupsim.scenario.routes:
        raise ValueError('Scenario must have routes configured')
    logger.info('Starting wagon pickup process')
    while True:
        collection_track_id, collection_wagons = yield from _wait_for_wagons_ready(popupsim)
        loco = yield from allocate_locomotive(popupsim)
        wagons_to_pickup = yield from _pickup_and_couple_wagons(popupsim, loco, collection_track_id, collection_wagons)
        if not wagons_to_pickup:
            yield popupsim.locomotives.put(loco)
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


def _process_track_batches(popupsim: PopupSim, workshop_track_id: str) -> Generator[Any]:
    """Process wagon batches for a single workshop track.
    
    Batch size = number of stations. Wagons can only be delivered when:
    1. Workshop track is completely empty
    2. All retrofit stations are empty
    """
    scenario = popupsim.scenario
    from models.scenario import LocoDeliveryStrategy

    while True:
        # Collect batch up to station count
        workshop = popupsim.workshop_capacity.workshops_by_track[workshop_track_id]
        batch_size = workshop.retrofit_stations
        batch_wagons = []
        retrofit_track_id = None
        
        for _ in range(batch_size):
            # Try to get wagon (non-blocking check if available)
            item = yield popupsim.wagons_ready_for_stations[workshop_track_id].get()
            track_id, wagons = item
            if retrofit_track_id is None:
                retrofit_track_id = track_id
            batch_wagons.extend(wagons)
            
            # Stop if no more wagons waiting
            if len(batch_wagons) >= batch_size:
                break
        
        if not batch_wagons or retrofit_track_id is None:
            continue
        
        # Wait until workshop track empty AND all stations empty
        while True:
            track_empty = popupsim.track_capacity.get_available_capacity(workshop_track_id) == \
                         popupsim.track_capacity.get_total_capacity(workshop_track_id)
            stations_empty = popupsim.workshop_capacity.get_available_stations(workshop_track_id) == \
                            workshop.retrofit_stations
            if track_empty and stations_empty:
                break
            yield popupsim.sim.delay(0.1)
        
        workshop_id = workshop.workshop_id
        batch = batch_wagons

        # Get locomotive
        loco = yield from allocate_locomotive(popupsim)
        
        # Strategy: RETURN_TO_PARKING (default)
        if scenario.loco_delivery_strategy == LocoDeliveryStrategy.RETURN_TO_PARKING:
            # Loco goes from parking to retrofit track
            logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, loco.track_id, retrofit_track_id)
            yield from move_locomotive(popupsim, loco, loco.track_id, retrofit_track_id)
        # else: DIRECT_DELIVERY - loco already at retrofit track from previous delivery

        # Travel to workshop via route
        route = find_route(scenario.routes, retrofit_track_id, workshop_id)
        if route and route.duration:
            logger.info(
                '🚂 ROUTE: Loco %s with %d wagons traveling [%s → %s] (duration: %.1f min)',
                loco.locomotive_id,
                len(batch),
                retrofit_track_id,
                workshop_id,
                route.duration,
            )
            for wagon in batch:
                wagon.status = WagonStatus.MOVING_TO_STATION
            yield from move_locomotive(popupsim, loco, loco.track_id, workshop_id)
        else:
            logger.warning('⚠️  No route found from %s to %s', retrofit_track_id, workshop_id)

        # Sequential decoupling and spawn processes (NOW at workshop)
        process_times = scenario.process_times
        for i, wagon in enumerate(batch):
            # Decouple wagon
            yield popupsim.sim.delay(process_times.wagon_decoupling_time)
            logger.info('✓ Wagon %s decoupled at station (t=%.1f)', wagon.wagon_id, popupsim.sim.current_time())

            # Spawn independent process for this wagon (already at workshop)
            popupsim.sim.run_process(process_single_wagon, popupsim, wagon, workshop_track_id)

            # Move to next station (if not last)
            if i < len(batch) - 1:
                yield popupsim.sim.delay(process_times.wagon_move_to_next_station)
                logger.info('🚂 Loco moved remaining wagons to next station')
        
        # Return loco based on strategy
        if scenario.loco_delivery_strategy == LocoDeliveryStrategy.RETURN_TO_PARKING:
            parking_track_id = popupsim.parking_tracks[0].id
            logger.info('🚂 ROUTE: Loco %s returning [%s → %s]', loco.locomotive_id, loco.track_id, parking_track_id)
            yield from move_locomotive(popupsim, loco, loco.track_id, parking_track_id)
        # else: DIRECT_DELIVERY - loco stays at workshop for next batch
        
        yield from release_locomotive(popupsim, loco)


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
    """Pickup retrofitted wagons in batches."""
    logger.info('Starting retrofitted wagon pickup process')

    # Process each track independently
    for track_id in popupsim.wagons_completed:
        popupsim.sim.run_process(_pickup_track_batches, popupsim, track_id)


def _pickup_track_batches(popupsim: PopupSim, workshop_track_id: str) -> Generator[Any]:
    """Pickup batches from a single workshop track."""
    retrofitted_track = popupsim.retrofitted_tracks[0]
    parking_tracks = popupsim.parking_tracks
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
        loco = yield from allocate_locomotive(popupsim)
        from_track = loco.track_id
        logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, from_track, workshop_track_id)
        yield from move_locomotive(popupsim, loco, from_track, workshop_track_id)

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

        # Remove from workshop track
        for wagon in batch:
            popupsim.track_capacity.remove_wagon(workshop_track_id, wagon.length)
            wagon.status = WagonStatus.MOVING
            wagon.source_track_id = workshop_track_id
            wagon.destination_track_id = retrofitted_track.id
            wagon.track_id = None

        # Travel to retrofitted track
        logger.info(
            '🚂 ROUTE: Loco %s traveling [%s → %s] with %d wagons',
            loco.locomotive_id,
            workshop_track_id,
            retrofitted_track.id,
            len(batch),
        )
        yield from move_locomotive(popupsim, loco, loco.track_id, retrofitted_track.id)

        # Decouple wagons
        yield from decouple_wagons(popupsim, loco, len(batch))

        # Add to retrofitted track
        for wagon in batch:
            popupsim.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
            wagon.track_id = retrofitted_track.id
            wagon.source_track_id = None
            wagon.destination_track_id = None
            wagon.status = WagonStatus.RETROFITTED
            logger.info('Wagon %s moved to retrofitted track', wagon.wagon_id)

        # Return loco to parking
        parking_track_id = parking_tracks[0].id
        yield from move_locomotive(popupsim, loco, loco.track_id, parking_track_id)
        loco.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)
        yield from release_locomotive(popupsim, loco)


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
        yield from execute_transport_job(popupsim, job)

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
    """Find wagons that can be moved to retrofit tracks with available stations."""
    wagons_to_pickup = []
    # Find retrofit tracks (not workshop tracks)
    retrofit_tracks = [t for t in popupsim.scenario.tracks if t.type == TrackType.RETROFIT]
    for wagon in collection_wagons:
        for retrofit_track in retrofit_tracks:
            retrofit_track_id = retrofit_track.id
            # Check if any workshop has capacity
            has_workshop_capacity = any(
                popupsim.workshop_capacity.get_available_stations(w.track_id) > 0
                for w in popupsim.workshops_queue
            )
            if has_workshop_capacity and popupsim.track_capacity.can_add_wagon(retrofit_track_id, wagon.length):
                wagons_to_pickup.append((wagon, retrofit_track_id))
                break
    return wagons_to_pickup


def _group_wagons_by_retrofit_track(wagons_to_pickup: list[tuple[Wagon, str]]) -> dict[str, list[Wagon]]:
    """Group wagons by their destination retrofit track."""
    wagons_by_retrofit: dict[str, list[Wagon]] = {}
    for wagon, retrofit_track_id in wagons_to_pickup:
        if retrofit_track_id not in wagons_by_retrofit:
            wagons_by_retrofit[retrofit_track_id] = []
        wagons_by_retrofit[retrofit_track_id].append(wagon)
    return wagons_by_retrofit


def move_locomotive(popupsim: PopupSim, loco: Locomotive, from_track: str, to_track: str) -> Generator[Any]:
    """Move locomotive from one track to another via route.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive to move.
    from_track : str
        Source track ID.
    to_track : str
        Destination track ID.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.MOVING)
    route = find_route(popupsim.scenario.routes, from_track, to_track)
    if route and route.duration:
        yield popupsim.sim.delay(route.duration)
    loco.track_id = to_track


def couple_wagons(popupsim: PopupSim, loco: Locomotive, wagon_count: int, coupler_type: CouplerType) -> Generator[Any]:
    """Couple wagons to locomotive.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive.
    wagon_count : int
        Number of wagons to couple.
    coupler_type : CouplerType
        Type of coupler on the wagons.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.COUPLING)
    process_times = popupsim.scenario.process_times
    time_per_wagon = (
        process_times.wagon_coupling_retrofitted_time
        if coupler_type == CouplerType.DAC
        else process_times.wagon_coupling_time
    )
    coupling_time = wagon_count * time_per_wagon
    yield popupsim.sim.delay(coupling_time)


def decouple_wagons(popupsim: PopupSim, loco: Locomotive, wagon_count: int) -> Generator[Any]:
    """Decouple wagons from locomotive.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive.
    wagon_count : int
        Number of wagons to decouple.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.DECOUPLING)
    decoupling_time = wagon_count * popupsim.scenario.process_times.wagon_decoupling_time
    yield popupsim.sim.delay(decoupling_time)


def allocate_locomotive(popupsim: PopupSim) -> Generator[Any]:
    """Allocate locomotive from pool with tracking.

    Yields
    ------
    Locomotive
        Allocated locomotive.
    """
    loco = cast(Locomotive, (yield popupsim.locomotives.get()))
    resource_id = getattr(loco, 'locomotive_id', getattr(loco, 'id', str(loco)))
    popupsim.locomotives.track_allocation(resource_id)
    return loco


def release_locomotive(popupsim: PopupSim, loco: Locomotive) -> Generator[Any]:
    """Release locomotive to pool with tracking.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive to release.

    Yields
    ------
    Any
        SimPy put event.
    """
    resource_id = getattr(loco, 'locomotive_id', getattr(loco, 'id', str(loco)))
    popupsim.locomotives.track_release(resource_id)
    yield popupsim.locomotives.put(loco)
