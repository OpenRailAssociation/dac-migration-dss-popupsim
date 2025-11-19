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

    Waits for first train to be processed, then continuously picks up wagons
    from collection tracks and moves them to retrofit track.
    """
    from .route_finder import find_route
    from models.track import TrackType

    scenario = popupsim.scenario
    process_times = scenario.process_times

    # Wait for first train to be fully processed
    if scenario.trains:
        first_train = scenario.trains[0]
        wait_time = (
            (first_train.arrival_time - scenario.start_date).total_seconds() / 60.0 +
            process_times.train_to_hump_delay +
            len(first_train.wagons) * process_times.wagon_hump_interval
        )
        yield popupsim.sim.delay(wait_time)

    logger.info('Starting wagon pickup process')

    # Find parking track (where locos start)
    parking_tracks = [t for t in scenario.tracks if t.type == TrackType.PARKING or t.type.value == 'resourceparking']
    if not parking_tracks:
        logger.warning('No resourceparking track found')
        return

    while True:
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

        # Pick wagons from this collection track
        wagons_to_pickup = []
        total_length = 0.0
        for wagon in collection_wagons:
            # Select retrofit track using strategy
            retrofit_track_id = popupsim.track_capacity.select_retrofit_track(wagon.length)
            if retrofit_track_id:
                wagons_to_pickup.append((wagon, retrofit_track_id))
                total_length += wagon.length

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

            # Decouple wagons at retrofit
            loco.status = LocoStatus.DECOUPLING
            decoupling_time = len(retrofit_wagons) * process_times.wagon_decoupling_time
            logger.debug('Loco %s decoupling %d wagons', loco.locomotive_id, len(retrofit_wagons))
            yield popupsim.sim.delay(decoupling_time)

            # Add to retrofit track
            for wagon in retrofit_wagons:
                popupsim.track_capacity.add_wagon(retrofit_track_id, wagon.length)
                wagon.track_id = retrofit_track_id
                wagon.status = WagonStatus.RETROFITTING
                logger.info('Wagon %s moved to retrofit track %s', wagon.wagon_id, retrofit_track_id)

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



