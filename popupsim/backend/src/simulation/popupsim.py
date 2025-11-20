from collections.abc import Generator
import logging
from typing import Any, cast

from models.locomotive import Locomotive
from models.locomotive import LocoStatus
from models.scenario import Scenario
from models.track import TrackType
from models.train import Train
from models.wagon import Wagon
from models.wagon import WagonStatus
from models.workshop import Workshop

from .jobs import TransportJob, execute_transport_job
from .resource_pool import ResourcePool
from .route_finder import find_route
from .sim_adapter import SimulationAdapter
from .track_capacity import TrackCapacityManager
from .workshop_capacity import WorkshopCapacityManager

logger = logging.getLogger('PopupSim')


def move_locomotive(popupsim: 'PopupSim', loco: Locomotive, from_track: str, to_track: str) -> Generator[Any]:
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


def couple_wagons(popupsim: 'PopupSim', loco: Locomotive, wagon_count: int) -> Generator[Any]:
    """Couple wagons to locomotive.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    loco : Locomotive
        The locomotive.
    wagon_count : int
        Number of wagons to couple.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    loco.record_status_change(popupsim.sim.current_time(), LocoStatus.COUPLING)
    coupling_time = wagon_count * popupsim.scenario.process_times.wagon_coupling_time
    yield popupsim.sim.delay(coupling_time)


def decouple_wagons(popupsim: 'PopupSim', loco: Locomotive, wagon_count: int) -> Generator[Any]:
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


def allocate_locomotive(popupsim: 'PopupSim') -> Generator[Any]:
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


def release_locomotive(popupsim: 'PopupSim', loco: Locomotive) -> Generator[Any]:
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


# WorkshopPool removed - workshops are managed via WorkshopCapacityManager
# which tracks station availability per retrofit track


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
        self.name: str = 'PopUpSim'
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
        if not scenario.workshops:
            raise ValueError('Scenario must have at least one workshop to simulate.')
        self.wagons_queue: list[Wagon] = []
        if not scenario.workshops:
            raise ValueError('Scenario must have at least one workshop to simulate.')
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
        self.workshop_capacity = WorkshopCapacityManager(self.workshops_queue)

        # Cache track lookups to avoid repeated list comprehensions
        if not scenario.tracks:
            raise ValueError('Scenario must have tracks configured')
        self.parking_tracks = [t for t in scenario.tracks 
                              if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
        self.retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]
        
        if not self.parking_tracks:
            raise ValueError('Scenario must have at least one parking track')
        if not self.retrofitted_tracks:
            raise ValueError('Scenario must have at least one retrofitted track')

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
        self.sim.run_process(process_retrofit_work, self)
        self.sim.run_process(pickup_retrofitted_wagons, self)
        self.sim.run_process(move_to_parking, self)

        self.sim.run(until)
        logger.info('Simulation completed.')


def process_train_arrivals(popupsim: PopupSim) -> Generator[Any]:
    """Generator function to simulate train arrivals.

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


def pickup_wagons_to_retrofit(popupsim: PopupSim) -> Generator[Any]:
    """Generator function to pickup wagons from collection and move to retrofit.

    Waits for each train to be fully processed before picking up its wagons.

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
    if not scenario.routes:
        raise ValueError('Scenario must have routes configured')

    logger.info('Starting wagon pickup process')

    # Track which trains have been processed
    processed_trains: set[str] = set()
    last_processed_count = 0

    # Use cached parking tracks
    parking_tracks = popupsim.parking_tracks

    while True:
        # Check if any new train has been fully processed
        current_processed_count = len(
            [
                train
                for train in scenario.trains
                if all(w in popupsim.wagons_queue or w.status == WagonStatus.REJECTED for w in train.wagons)
            ]
        )

        if current_processed_count > last_processed_count:
            logger.info('Train fully processed, %d trains ready for pickup', current_processed_count)
            last_processed_count = current_processed_count

        # Only pickup wagons from fully processed trains
        if last_processed_count == 0:
            yield popupsim.sim.delay(1.0)
            continue

        # Group wagons by collection track
        wagons_by_track: dict[str, list[Wagon]] = {}
        for wagon in popupsim.wagons_queue:
            if wagon.status == WagonStatus.SELECTED and wagon.track_id:
                if wagon.track_id not in wagons_by_track:
                    wagons_by_track[wagon.track_id] = []
                wagons_by_track[wagon.track_id].append(wagon)

        if not wagons_by_track:
            yield popupsim.sim.delay(1.0)  # Wait 1 minute and check again
            continue

        # Get locomotive from pool (blocks until available)
        loco = yield from allocate_locomotive(popupsim)

        # Pick first collection track with wagons
        collection_track_id = list(wagons_by_track.keys())[0]
        collection_wagons = wagons_by_track[collection_track_id]

        # Travel from loco position to collection track
        from_track = loco.track_id
        logger.info('🚂 ROUTE: Loco %s traveling [%s → %s]', loco.locomotive_id, from_track, collection_track_id)
        yield from move_locomotive(popupsim, loco, from_track, collection_track_id)

        # Pick wagons from this collection track based on available retrofit stations
        wagons_to_pickup = []
        for wagon in collection_wagons:
            # Find retrofit track with available stations
            for retrofit_track_id in popupsim.workshop_capacity.workshops_by_track.keys():
                available_stations = popupsim.workshop_capacity.get_available_stations(retrofit_track_id)
                if available_stations > 0 and popupsim.track_capacity.can_add_wagon(retrofit_track_id, wagon.length):
                    wagons_to_pickup.append((wagon, retrofit_track_id))
                    break

        if not wagons_to_pickup:
            yield popupsim.locomotives.put(loco)
            yield popupsim.sim.delay(1.0)
            continue

        # Couple wagons
        logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons_to_pickup))
        yield from couple_wagons(popupsim, loco, len(wagons_to_pickup))

        # Remove from collection track
        for wagon, retrofit_track_id in wagons_to_pickup:
            popupsim.track_capacity.remove_wagon(collection_track_id, wagon.length)
            wagon.status = WagonStatus.MOVING
            wagon.source_track_id = collection_track_id
            wagon.destination_track_id = retrofit_track_id
            wagon.track_id = None

        # Group wagons by retrofit track destination
        wagons_by_retrofit: dict[str, list[Wagon]] = {}
        for wagon, retrofit_track_id in wagons_to_pickup:
            if retrofit_track_id not in wagons_by_retrofit:
                wagons_by_retrofit[retrofit_track_id] = []
            wagons_by_retrofit[retrofit_track_id].append(wagon)

        # Deliver to each retrofit track
        for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
            # Travel from collection to retrofit
            from_track = loco.track_id
            logger.info('🚂 ROUTE: Loco %s traveling [%s → %s] with %d wagons', 
                       loco.locomotive_id, from_track, retrofit_track_id, len(retrofit_wagons))
            yield from move_locomotive(popupsim, loco, from_track, retrofit_track_id)

            # Check available retrofit stations and limit wagons
            available_stations = popupsim.workshop_capacity.get_available_stations(retrofit_track_id)
            wagons_to_deliver = retrofit_wagons[:available_stations]

            if not wagons_to_deliver:
                continue

            # Decouple wagons at retrofit
            logger.debug('Loco %s decoupling %d wagons to %d stations', loco.locomotive_id, len(wagons_to_deliver), available_stations)
            yield from decouple_wagons(popupsim, loco, len(wagons_to_deliver))

            # Add wagons to retrofit track (not yet at stations)
            for wagon in wagons_to_deliver:
                popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
                wagon.track_id = retrofit_track_id
                wagon.source_track_id = None
                wagon.destination_track_id = None
                wagon.status = WagonStatus.ON_RETROFIT_TRACK
                logger.info(
                    'Wagon %s delivered to retrofit track %s (waiting for station)', wagon.wagon_id, retrofit_track_id
                )

        # Return loco to parking
        parking_track_id = parking_tracks[0].id
        logger.debug('Loco %s returning to parking', loco.locomotive_id)
        yield from move_locomotive(popupsim, loco, loco.track_id, parking_track_id)
        loco.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)
        yield from release_locomotive(popupsim, loco)


def move_wagons_to_stations(popupsim: PopupSim) -> Generator[Any]:
    """Move wagons from retrofit track to workshop stations using routes.

    Wagons wait on retrofit track until a station becomes available,
    then travel via route to the workshop station location.

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
    if not scenario.routes:
        raise ValueError('Scenario must have routes configured')

    logger.info('Starting wagon-to-station movement process')

    while True:
        # Check each retrofit track for waiting wagons
        for retrofit_track_id, workshop in popupsim.workshop_capacity.workshops_by_track.items():
            # Find wagons waiting on this retrofit track
            waiting_wagons = [
                w
                for w in popupsim.wagons_queue
                if w.track_id == retrofit_track_id and w.status == WagonStatus.ON_RETROFIT_TRACK
            ]

            if not waiting_wagons:
                continue

            # Check available stations
            available_stations = popupsim.workshop_capacity.get_available_stations(retrofit_track_id)

            if available_stations > 0:
                wagon = waiting_wagons[0]  # FIFO

                # Move wagon from track to workshop via route
                wagon.status = WagonStatus.MOVING_TO_STATION
                workshop_id = workshop.workshop_id

                route_to_workshop = find_route(scenario.routes, retrofit_track_id, workshop_id)
                if route_to_workshop and route_to_workshop.duration:
                    logger.info(
                        '🚂 ROUTE: Wagon %s traveling [%s → %s] via route (duration: %.1f min)',
                        wagon.wagon_id,
                        retrofit_track_id,
                        workshop_id,
                        route_to_workshop.duration,
                    )
                    yield popupsim.sim.delay(route_to_workshop.duration)
                else:
                    logger.warning(
                        '⚠️  No route found from %s to %s for wagon %s', retrofit_track_id, workshop_id, wagon.wagon_id
                    )

                # Occupy station and start retrofit
                popupsim.workshop_capacity.occupy_stations(retrofit_track_id, 1)
                wagon.status = WagonStatus.RETROFITTING
                logger.info('✓ Wagon %s arrived at workshop %s (station occupied)', wagon.wagon_id, workshop_id)

        # NOTE: Polling with 0.5-minute interval is acceptable for MVP:
        # - Simulation time is cheap (not real-time)
        # - Provides responsive station allocation
        # - Simplifies coordination between processes
        yield popupsim.sim.delay(0.5)


def process_retrofit_work(popupsim: PopupSim) -> Generator[Any]:
    """Generator function to process retrofit work and release stations.

    Monitors wagons in RETROFITTING status and releases stations after work completes.

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

    logger.info('Starting retrofit work processor')

    while True:
        # Find wagons that are retrofitting
        retrofitting_wagons = [
            w for w in popupsim.wagons_queue if w.status == WagonStatus.RETROFITTING and not w.retrofit_start_time
        ]

        if retrofitting_wagons:
            for wagon in retrofitting_wagons:
                # Start retrofit work
                wagon.retrofit_start_time = popupsim.sim.current_time()
                logger.debug('Wagon %s started retrofit at t=%.1f', wagon.wagon_id, wagon.retrofit_start_time)
                # Schedule completion
                popupsim.sim.run_process(complete_retrofit, popupsim, wagon, process_times.wagon_retrofit_time)

        # NOTE: Polling with 1-minute interval is acceptable for MVP:
        # - Matches business granularity (retrofit work is 30+ minutes)
        # - Avoids complexity of event coordination
        # - Simulation time is not a bottleneck
        yield popupsim.sim.delay(1.0)


def complete_retrofit(popupsim: PopupSim, wagon: Wagon, retrofit_duration: float) -> Generator[Any]:
    """Complete retrofit work for a wagon. Station remains occupied until pickup.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
    wagon : Wagon
        The wagon being retrofitted.
    retrofit_duration : float
        Duration of retrofit work in minutes.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    yield popupsim.sim.delay(retrofit_duration)

    wagon.status = WagonStatus.RETROFITTED
    wagon.retrofit_end_time = popupsim.sim.current_time()
    wagon.needs_retrofit = False  # Mark as retrofitted to avoid re-processing
    logger.info(
        'Wagon %s retrofit completed at t=%s, needs_retrofit set to False', wagon.wagon_id, wagon.retrofit_end_time
    )


def pickup_retrofitted_wagons(popupsim: PopupSim) -> Generator[Any]:
    """Pickup retrofitted wagons and move to retrofitted track, releasing stations.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.

    Yields
    ------
    Any
        SimPy timeout events.
    """
    yield popupsim.sim.delay(20.0)  # Wait for first retrofit to complete
    logger.info('Starting retrofitted wagon pickup process')
    retrofitted_track = popupsim.retrofitted_tracks[0]

    while True:
        # Group retrofitted wagons by retrofit track (only those still on retrofit tracks)
        retrofitted_by_track: dict[str, list[Wagon]] = {}
        for wagon in popupsim.wagons_queue:
            # Only pick up wagons that are RETROFITTED and on a retrofit track (not retrofitted track)
            if (wagon.status == WagonStatus.RETROFITTED and wagon.track_id and 
                wagon.track_id != retrofitted_track.id and wagon.track_id.startswith('retrofit_')):
                if wagon.track_id not in retrofitted_by_track:
                    retrofitted_by_track[wagon.track_id] = []
                retrofitted_by_track[wagon.track_id].append(wagon)

        if not retrofitted_by_track:
            yield popupsim.sim.delay(1.0)
            continue

        # Pick first retrofit track with completed wagons (pick up one wagon at a time)
        retrofit_track_id = list(retrofitted_by_track.keys())[0]
        wagons_to_pickup = [retrofitted_by_track[retrofit_track_id][0]]

        # Release stations before transport
        for wagon in wagons_to_pickup:
            popupsim.workshop_capacity.release_stations(retrofit_track_id, 1)
            logger.info('Station released on %s for wagon %s', retrofit_track_id, wagon.wagon_id)

        # Execute transport job
        job = TransportJob(
            wagons=wagons_to_pickup,
            from_track=retrofit_track_id,
            to_track=retrofitted_track.id,
        )
        yield from execute_transport_job(popupsim, job)

        # Update final wagon status
        for wagon in wagons_to_pickup:
            wagon.status = WagonStatus.RETROFITTED
            logger.info('Wagon %s moved to retrofitted track', wagon.wagon_id)


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
            w for w in popupsim.wagons_queue
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
        wagons_to_move = [w for w in wagons_on_retrofitted 
                         if popupsim.track_capacity.can_add_wagon(parking_track.id, w.length)]

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
