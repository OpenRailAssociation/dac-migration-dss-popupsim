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
        return locomotive

    def release_locomotive(self, locomotive: Locomotive) -> None:
        """Release a locomotive back to the pool.

        Parameters
        ----------
        locomotive : Train
            The locomotive to release back to the pool.
        """
        loco = self.occupied_locomotives.pop(locomotive.id)
        self.available_locomotives[loco.id] = loco

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
                strategy=scenario.track_selection_strategy
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


def move_wagons_from_collection_to_retrofit(popupsim: PopupSim):
    """Generator function to move wagons from collection to retrofit.

    This function moves wagons from the collection to the retrofit station.
    It yields wagon movements as Wagon objects.

    Parameters
    ----------
    sim : SimulationAdapter
        The simulation adapter used to manage the simulation.

    Yields
    ------
    Wagon
        A wagon movement as a Wagon object.
    """
    scenario = popupsim.scenario
    logger.info('Starting wagon movement generator for scenario %s', scenario.scenario_id)
    for wagon in popupsim.wagons_queue:
        logger.debug('Waiting for next wagon movement at %s', wagon.arrival_time)
        yield popupsim.sim.delay((wagon.arrival_time - scenario.start_date).total_seconds() / 60.0)
        logger.debug('Wagon %s arrived at %s', wagon.wagon_id, wagon.arrival_time)



