import logging

from models.locomotive import Locomotive
from models.locomotive import LocoStatus
from models.scenario import Scenario
from models.train import Train
from models.wagon import Wagon
from models.wagon import WagonStatus
from models.workshop import Workshop

from .sim_adapter import SimulationAdapter
from .track_capacity import TrackCapacityManager
from .workshop_capacity import WorkshopCapacityManager

logger = logging.getLogger('PopupSim')

class LocomotivePool:
    """Pool of locomotives for managing available locomotives in the simulation.

    This class manages a collection of locomotives, allowing for allocation
    and release of locomotives as needed during the simulation.
    """

    def __init__(self, sim, locomotives: list[Locomotive], poll_interval: float = 0.01) -> None:
        self.available_locomotives = {}
        for loco in locomotives:
            self.available_locomotives[loco.locomotive_id] = loco
        self.occupied_locomotives = {}
        self.poll = float(poll_interval)
        self.sim = sim

    # nested function to return a fresh generator every time it's called
    def acquire(self):
        def _acq():
            while len(self.available_locomotives) >= 1:
                yield self.sim.delay(self.poll)
            locomotive = self.allocate_locomotive()
            self.occupied_locomotives[locomotive.id] = locomotive

        return _acq()

    def allocate_locomotive(self) -> Locomotive | None:
        """Allocate an available locomotive from the pool.

        Returns
        -------
        Train | None
            An available locomotive if one exists, otherwise None.
        """
        if not self.available_locomotives:
            return None
        key_of_last_loco = list(self.available_locomotives.keys())[-1]
        locomotive = self.available_locomotives.pop(key_of_last_loco)
        self.occupied_locomotives[locomotive.locomotive_id] = locomotive
        return locomotive

    def release_locomotive(self, locomotive: Locomotive) -> None:
        """Release a locomotive back to the pool.

        Parameters
        ----------
        locomotive : Train
            The locomotive to release back to the pool.
        """
        loco = self.occupied_locomotives.pop(locomotive.locomotive_id)
        self.available_locomotives[loco.locomotive_id] = loco

class WorkshopPool:
    """Pool of workshops for managing available workshops in the simulation.

    This class manages a collection of workshops, allowing for allocation
    and release of workshops as needed during the simulation.
    """

    def __init__(self, sim, workshops: list[Workshop], poll_interval: float = 0.01) -> None:
        self.available_workshops = {}
        self.occupied_workshops = {}
        for workshop in workshops:
            self.available_workshops[workshop.workshop_id] = workshop

        self.poll = float(poll_interval)
        self.sim = sim

    # nested function to return a fresh generator every time it's called
    def acquire(self):
        def _acq():
            while len(self.available_workshops) >= 1:
                yield self.sim.delay(self.poll)
            workshop = self.allocate_workshop()
            self.occupied_workshops[workshop.workshop_id] = workshop
            return workshop

        return _acq()


    def allocate_workshop(self) -> Workshop | None:
        """Allocate an available workshop from the pool.

        Returns
        -------
        Workshop | None
            An available workshop if one exists, otherwise None.
        """
        if not self.available_workshops:
            return None
        key_of_last_workshop = list(self.available_workshops.keys())[-1]
        workshop = self.available_workshops.pop(key_of_last_workshop)
        return workshop

    def release_workshop(self, workshop: Workshop) -> None:
        """Release a workshop back to the pool.

        Parameters
        ----------
        workshop : Workshop
            The workshop to release back to the pool.
        """
        released_workshop = self.occupied_workshops.pop(workshop.workshop_id)
        self.available_workshops[released_workshop.workshop_id] = released_workshop


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
        if not scenario.trains:
            raise ValueError('Scenario must have at least one train to simulate.')
        self.trains_queue: list[Train] = scenario.trains
        if not scenario.workshops:
            raise ValueError('Scenario must have at least one workshop to simulate.')
        self.wagons_queue: list[Wagon] = []
        if not scenario.workshops:
            raise ValueError('Scenario must have at least one workshop to simulate.')
        self.workshops_queue: list[Workshop] = scenario.workshops

        self.locomotives = LocomotivePool(self.sim, self.locomotives_queue)
        self.workshops = WorkshopPool(self.sim, self.workshops_queue)

        # Initialize track capacity management
        if scenario.tracks and scenario.topology:
            self.track_capacity = TrackCapacityManager(
                scenario.tracks,
                scenario.topology,
                collection_strategy=scenario.track_selection_strategy,
                retrofit_strategy=scenario.retrofit_selection_strategy
            )
        else:
            raise ValueError('Scenario must have tracks and topology for capacity management.')
        
        # Initialize workshop capacity management
        self.workshop_capacity = WorkshopCapacityManager(self.workshops_queue)

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
        self.sim.run_process(process_retrofit_work, self)
        self.sim.run_process(pickup_retrofitted_wagons, self)
        self.sim.run_process(move_to_parking, self)

        self.sim.run(until)
        logger.info('Simulation completed.')

def process_train_arrivals(popupsim: PopupSim):
    """Generator function to simulate train arrivals.

    This function generates train arrivals based on the provided scenario.
    It yields train arrivals as Train objects.

    Parameters
    ----------
    sim : SimulationAdapter
        The simulation adapter used to manage the simulation.

    Yields
    ------
    Train
        A train arrival as a Train object.
    """
    scenario = popupsim.scenario
    process_times = scenario.process_times
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


def pickup_wagons_to_retrofit(popupsim: PopupSim):
    """Generator function to pickup wagons from collection and move to retrofit.

    Waits for each train to be fully processed before picking up its wagons.
    """
    from .route_finder import find_route
    from models.track import TrackType

    scenario = popupsim.scenario
    process_times = scenario.process_times

    logger.info('Starting wagon pickup process')
    
    # Track which trains have been processed
    processed_trains = set()
    last_processed_count = 0

    # Find parking track (where locos start)
    parking_tracks = [t for t in scenario.tracks if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
    if not parking_tracks:
        logger.warning('No resourceparking track found')
        return

    while True:
        # Check if any new train has been fully processed
        current_processed_count = sum(1 for train in scenario.trains 
                                     if all(w in popupsim.wagons_queue or w.status == WagonStatus.REJECTED 
                                           for w in train.wagons))
        
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

        # Get available locomotive
        loco = popupsim.locomotives.allocate_locomotive()
        if not loco:
            yield popupsim.sim.delay(1.0)
            continue

        # Pick first collection track with wagons
        collection_track_id = list(wagons_by_track.keys())[0]
        collection_wagons = wagons_by_track[collection_track_id]

        # Travel from loco position to collection track
        loco.status = LocoStatus.MOVING
        route_to_collection = find_route(scenario.routes, loco.track_id, collection_track_id)
        if route_to_collection and route_to_collection.duration:
            logger.debug('Loco %s traveling to collection track %s', loco.locomotive_id, collection_track_id)
            yield popupsim.sim.delay(route_to_collection.duration)
        loco.track_id = collection_track_id

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
            popupsim.locomotives.release_locomotive(loco)
            yield popupsim.sim.delay(1.0)
            continue

        # Couple wagons
        loco.status = LocoStatus.COUPLING
        coupling_time = len(wagons_to_pickup) * process_times.wagon_coupling_time
        logger.debug('Loco %s coupling %d wagons', loco.locomotive_id, len(wagons_to_pickup))
        yield popupsim.sim.delay(coupling_time)

        # Remove from collection track
        for wagon, _ in wagons_to_pickup:
            popupsim.track_capacity.remove_wagon(collection_track_id, wagon.length)
            wagon.status = WagonStatus.MOVING

        # Group wagons by retrofit track destination
        wagons_by_retrofit: dict[str, list[Wagon]] = {}
        for wagon, retrofit_track_id in wagons_to_pickup:
            if retrofit_track_id not in wagons_by_retrofit:
                wagons_by_retrofit[retrofit_track_id] = []
            wagons_by_retrofit[retrofit_track_id].append(wagon)

        # Deliver to each retrofit track
        for retrofit_track_id, retrofit_wagons in wagons_by_retrofit.items():
            # Travel from collection to retrofit
            loco.status = LocoStatus.MOVING
            route_to_retrofit = find_route(scenario.routes, loco.track_id, retrofit_track_id)
            if route_to_retrofit and route_to_retrofit.duration:
                logger.debug('Loco %s traveling to retrofit %s with %d wagons', loco.locomotive_id, retrofit_track_id, len(retrofit_wagons))
                yield popupsim.sim.delay(route_to_retrofit.duration)
            loco.track_id = retrofit_track_id

            # Check available retrofit stations and limit wagons
            available_stations = popupsim.workshop_capacity.get_available_stations(retrofit_track_id)
            wagons_to_deliver = retrofit_wagons[:available_stations]
            
            if not wagons_to_deliver:
                continue
            
            # Decouple wagons at retrofit
            loco.status = LocoStatus.DECOUPLING
            decoupling_time = len(wagons_to_deliver) * process_times.wagon_decoupling_time
            logger.debug('Loco %s decoupling %d wagons to %d stations', loco.locomotive_id, len(wagons_to_deliver), available_stations)
            yield popupsim.sim.delay(decoupling_time)

            # Occupy retrofit stations and add to track
            popupsim.workshop_capacity.occupy_stations(retrofit_track_id, len(wagons_to_deliver))
            for wagon in wagons_to_deliver:
                popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
                wagon.track_id = retrofit_track_id
                wagon.status = WagonStatus.RETROFITTING
                logger.info('Wagon %s moved to retrofit track %s (station occupied)', wagon.wagon_id, retrofit_track_id)

        # Return loco to parking
        loco.status = LocoStatus.MOVING
        parking_track_id = parking_tracks[0].id
        route_to_parking = find_route(scenario.routes, loco.track_id, parking_track_id)
        if route_to_parking and route_to_parking.duration:
            logger.debug('Loco %s returning to parking', loco.locomotive_id)
            yield popupsim.sim.delay(route_to_parking.duration)
        loco.track_id = parking_track_id
        loco.status = LocoStatus.PARKING
        popupsim.locomotives.release_locomotive(loco)


def process_retrofit_work(popupsim: PopupSim):
    """Generator function to process retrofit work and release stations.
    
    Monitors wagons in RETROFITTING status and releases stations after work completes.
    """
    scenario = popupsim.scenario
    process_times = scenario.process_times
    
    logger.info('Starting retrofit work processor')
    
    while True:
        # Find wagons that are retrofitting
        retrofitting_wagons = [
            w for w in popupsim.wagons_queue 
            if w.status == WagonStatus.RETROFITTING and not w.retrofit_start_time
        ]
        
        if retrofitting_wagons:
            for wagon in retrofitting_wagons:
                # Start retrofit work
                wagon.retrofit_start_time = popupsim.sim.current_time()
                logger.debug('Wagon %s started retrofit at t=%.1f', wagon.wagon_id, wagon.retrofit_start_time)
                # Schedule completion
                popupsim.sim.run_process(complete_retrofit, popupsim, wagon, process_times.wagon_retrofit_time)
        
        yield popupsim.sim.delay(1.0)


def complete_retrofit(popupsim: PopupSim, wagon: Wagon, retrofit_duration: float):
    """Complete retrofit work for a wagon. Station remains occupied until pickup."""
    yield popupsim.sim.delay(retrofit_duration)
    
    wagon.status = WagonStatus.RETROFITTED
    wagon.retrofit_end_time = popupsim.sim.current_time()
    wagon.needs_retrofit = False  # Mark as retrofitted to avoid re-processing
    logger.info('Wagon %s retrofit completed at t=%.1f, needs_retrofit set to False', 
               wagon.wagon_id, wagon.retrofit_end_time)


def pickup_retrofitted_wagons(popupsim: PopupSim):
    """Pickup retrofitted wagons and move to retrofitted track, releasing stations."""
    from .route_finder import find_route
    from models.track import TrackType
    
    scenario = popupsim.scenario
    process_times = scenario.process_times
    
    # Wait for first retrofit to potentially complete
    yield popupsim.sim.delay(20.0)
    
    logger.info('Starting retrofitted wagon pickup process')
    
    # Find parking and retrofitted tracks
    parking_tracks = [t for t in scenario.tracks if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
    retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]
    
    if not parking_tracks or not retrofitted_tracks:
        logger.warning('No parking or retrofitted track found')
        return
    
    retrofitted_track = retrofitted_tracks[0]
    
    while True:
        # Group retrofitted wagons by retrofit track
        retrofitted_by_track: dict[str, list[Wagon]] = {}
        for wagon in popupsim.wagons_queue:
            if wagon.status == WagonStatus.RETROFITTED and wagon.track_id:
                if wagon.track_id not in retrofitted_by_track:
                    retrofitted_by_track[wagon.track_id] = []
                retrofitted_by_track[wagon.track_id].append(wagon)
        
        if not retrofitted_by_track:
            yield popupsim.sim.delay(1.0)
            continue
        
        # Get available locomotive
        loco = popupsim.locomotives.allocate_locomotive()
        if not loco:
            yield popupsim.sim.delay(1.0)
            continue
        
        # Pick first retrofit track with completed wagons
        retrofit_track_id = list(retrofitted_by_track.keys())[0]
        wagons_to_pickup = retrofitted_by_track[retrofit_track_id]
        
        # Travel to retrofit track
        loco.status = LocoStatus.MOVING
        route_to_retrofit = find_route(scenario.routes, loco.track_id, retrofit_track_id)
        if route_to_retrofit and route_to_retrofit.duration:
            logger.debug('Loco %s traveling to retrofit track %s for pickup', loco.locomotive_id, retrofit_track_id)
            yield popupsim.sim.delay(route_to_retrofit.duration)
        loco.track_id = retrofit_track_id
        
        # Couple wagons
        loco.status = LocoStatus.COUPLING
        coupling_time = len(wagons_to_pickup) * process_times.wagon_coupling_time
        logger.debug('Loco %s coupling %d retrofitted wagons', loco.locomotive_id, len(wagons_to_pickup))
        yield popupsim.sim.delay(coupling_time)
        
        # Remove from retrofit track and release stations
        for wagon in wagons_to_pickup:
            popupsim.track_capacity.remove_wagon(retrofit_track_id, wagon.length)
            popupsim.workshop_capacity.release_stations(retrofit_track_id, 1)
            wagon.status = WagonStatus.MOVING
            logger.info('Station released on %s for wagon %s', retrofit_track_id, wagon.wagon_id)
        
        # Travel to retrofitted track
        loco.status = LocoStatus.MOVING
        route_to_retrofitted = find_route(scenario.routes, retrofit_track_id, retrofitted_track.id)
        if route_to_retrofitted and route_to_retrofitted.duration:
            logger.debug('Loco %s traveling to retrofitted track with %d wagons', loco.locomotive_id, len(wagons_to_pickup))
            yield popupsim.sim.delay(route_to_retrofitted.duration)
        loco.track_id = retrofitted_track.id
        
        # Decouple wagons
        loco.status = LocoStatus.DECOUPLING
        decoupling_time = len(wagons_to_pickup) * process_times.wagon_decoupling_time
        logger.debug('Loco %s decoupling %d wagons at retrofitted track', loco.locomotive_id, len(wagons_to_pickup))
        yield popupsim.sim.delay(decoupling_time)
        
        # Add to retrofitted track
        for wagon in wagons_to_pickup:
            popupsim.track_capacity.add_wagon(retrofitted_track.id, wagon.length)
            wagon.track_id = retrofitted_track.id
            wagon.status = WagonStatus.RETROFITTED
            logger.info('Wagon %s moved to retrofitted track', wagon.wagon_id)
        
        # Return loco to parking
        loco.status = LocoStatus.MOVING
        parking_track_id = parking_tracks[0].id
        route_to_parking = find_route(scenario.routes, loco.track_id, parking_track_id)
        if route_to_parking and route_to_parking.duration:
            logger.debug('Loco %s returning to parking', loco.locomotive_id)
            yield popupsim.sim.delay(route_to_parking.duration)
        loco.track_id = parking_track_id
        loco.status = LocoStatus.PARKING
        popupsim.locomotives.release_locomotive(loco)


def move_to_parking(popupsim: PopupSim):
    """Move wagons from retrofitted track to parking tracks (sequential fill)."""
    from .route_finder import find_route
    from models.track import TrackType
    
    scenario = popupsim.scenario
    process_times = scenario.process_times
    
    # Wait for first wagons to reach retrofitted track
    yield popupsim.sim.delay(60.0)
    
    logger.info('Starting move to parking process')
    
    # Find retrofitted and parking tracks
    retrofitted_tracks = [t for t in scenario.tracks if t.type == TrackType.RETROFITTED]
    parking_tracks = [t for t in scenario.tracks if t.type == TrackType.PARKING]
    
    if not retrofitted_tracks or not parking_tracks:
        logger.warning('No retrofitted or parking tracks found')
        return
    
    retrofitted_track = retrofitted_tracks[0]
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
        
        # Get available locomotive
        loco = popupsim.locomotives.allocate_locomotive()
        if not loco:
            yield popupsim.sim.delay(1.0)
            continue
        
        # Travel to retrofitted track
        loco.status = LocoStatus.MOVING
        route_to_retrofitted = find_route(scenario.routes, loco.track_id, retrofitted_track.id)
        if route_to_retrofitted and route_to_retrofitted.duration:
            logger.debug('Loco %s traveling to retrofitted track', loco.locomotive_id)
            yield popupsim.sim.delay(route_to_retrofitted.duration)
        loco.track_id = retrofitted_track.id
        
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
            popupsim.locomotives.release_locomotive(loco)
            yield popupsim.sim.delay(1.0)
            continue
        
        # Pick wagons that fit on selected parking track
        wagons_to_move = []
        for wagon in wagons_on_retrofitted:
            if popupsim.track_capacity.can_add_wagon(parking_track.id, wagon.length):
                wagons_to_move.append(wagon)
        
        if not wagons_to_move:
            current_parking_index = (current_parking_index + 1) % len(parking_tracks)
            popupsim.locomotives.release_locomotive(loco)
            yield popupsim.sim.delay(1.0)
            continue
        
        # Couple wagons
        loco.status = LocoStatus.COUPLING
        coupling_time = len(wagons_to_move) * process_times.wagon_coupling_time
        logger.debug('Loco %s coupling %d wagons for parking', loco.locomotive_id, len(wagons_to_move))
        yield popupsim.sim.delay(coupling_time)
        
        # Remove from retrofitted track
        for wagon in wagons_to_move:
            popupsim.track_capacity.remove_wagon(retrofitted_track.id, wagon.length)
            wagon.status = WagonStatus.MOVING
        
        # Travel to parking track
        loco.status = LocoStatus.MOVING
        route_to_parking = find_route(scenario.routes, retrofitted_track.id, parking_track.id)
        if route_to_parking and route_to_parking.duration:
            logger.debug('Loco %s traveling to parking %s with %d wagons', loco.locomotive_id, parking_track.id, len(wagons_to_move))
            yield popupsim.sim.delay(route_to_parking.duration)
        loco.track_id = parking_track.id
        
        # Decouple wagons
        loco.status = LocoStatus.DECOUPLING
        decoupling_time = len(wagons_to_move) * process_times.wagon_decoupling_time
        logger.debug('Loco %s decoupling %d wagons at parking', loco.locomotive_id, len(wagons_to_move))
        yield popupsim.sim.delay(decoupling_time)
        
        # Add to parking track
        for wagon in wagons_to_move:
            popupsim.track_capacity.add_wagon(parking_track.id, wagon.length)
            wagon.track_id = parking_track.id
            wagon.status = WagonStatus.PARKING
            logger.info('Wagon %s moved to parking track %s', wagon.wagon_id, parking_track.id)
        
        # Check if current parking track is full, move to next
        remaining_wagons = [w for w in wagons_on_retrofitted if w not in wagons_to_move]
        if remaining_wagons and not any(popupsim.track_capacity.can_add_wagon(parking_track.id, w.length) for w in remaining_wagons):
            current_parking_index = (current_parking_index + 1) % len(parking_tracks)
            logger.debug('Parking track %s full, switching to next', parking_track.id)
        
        loco.status = LocoStatus.PARKING
        popupsim.locomotives.release_locomotive(loco)
