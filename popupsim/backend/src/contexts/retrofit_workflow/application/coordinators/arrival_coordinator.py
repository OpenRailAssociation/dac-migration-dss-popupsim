"""Arrival coordinator for managing train arrivals and wagon processing.

This module provides coordination services for handling train arrivals in the
DAC migration simulation system. It manages the arrival process, wagon creation,
and initial classification operations.
"""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ArrivalCoordinatorConfig
from contexts.retrofit_workflow.domain.aggregates.train_aggregate import Train
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType


class ArrivalCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinator for managing train arrivals and initial wagon processing.

    This coordinator handles the arrival phase of the DAC migration process,
    managing train scheduling, wagon entity creation, and initial classification
    operations. It serves as the entry point for wagons into the simulation system.

    Responsibilities
    ----------------
    - Schedule and process train arrivals based on scenario configuration
    - Create wagon entities from train configuration data
    - Manage initial wagon classification and status transitions
    - Place classified wagons on collection tracks for further processing
    - Publish arrival events for system monitoring and coordination

    Attributes
    ----------
    env : simpy.Environment
        SimPy simulation environment for process scheduling
    collection_queue : simpy.FilterStore
        Queue for storing classified wagons awaiting collection
    event_publisher : callable
        Function for publishing domain events to the system
    trains : list[Train]
        List of scheduled trains for tracking and management

    Examples
    --------
    >>> config = ArrivalCoordinatorConfig(env, collection_queue, event_publisher)
    >>> coordinator = ArrivalCoordinator(config)
    >>> coordinator.schedule_train('TRAIN_001', 60.0, wagon_configs)
    """

    def __init__(self, config: ArrivalCoordinatorConfig) -> None:
        """Initialize the arrival coordinator with configuration.

        Parameters
        ----------
        config : ArrivalCoordinatorConfig
            Configuration object containing required dependencies and settings

        Notes
        -----
        The configuration object provides all necessary dependencies including
        the simulation environment, collection queue, and event publisher.
        """
        self.env = config.env
        self.collection_queue = config.collection_queue
        self.event_publisher = config.event_publisher
        self.trains: list[Train] = []

    def schedule_train(
        self,
        train_id: str,
        arrival_time: float,
        wagon_configs: list[dict[str, Any]],
    ) -> None:
        """Schedule a train arrival with specified wagons and timing.

        Creates wagon entities from configuration data, assembles them into
        a train aggregate, and schedules the arrival process for execution
        at the specified simulation time.

        Parameters
        ----------
        train_id : str
            Unique identifier for the arriving train
        arrival_time : float
            Simulation time when the train should arrive (in simulation ticks)
        wagon_configs : list[dict[str, Any]]
            List of wagon configuration dictionaries containing wagon specifications

        Notes
        -----
        Wagon configurations should contain:
        - 'id': Unique wagon identifier
        - 'length': Wagon length in meters (defaults to 15.0)
        - 'is_loaded': Whether wagon is loaded (optional, defaults to False)
        - 'needs_retrofit': Whether wagon needs retrofit (optional, defaults to True)

        Wagons are filtered: only unloaded wagons that need retrofit are processed.
        Loaded wagons or wagons that don't need retrofit are rejected.

        The method creates a SimPy process that will execute the arrival
        at the specified time, handling all necessary coordination.

        Examples
        --------
        >>> wagon_configs = [
        ...     {'id': 'W001', 'length': 18.5, 'is_loaded': False, 'needs_retrofit': True},
        ...     {'id': 'W002', 'length': 16.0, 'is_loaded': True, 'needs_retrofit': True},  # Rejected
        ...     {'id': 'W003', 'length': 20.0, 'is_loaded': False, 'needs_retrofit': False},  # Rejected
        ... ]
        >>> coordinator.schedule_train('TRAIN_001', 120.0, wagon_configs)
        """
        # Filter wagons and log rejections
        eligible_configs = []
        for cfg in wagon_configs:
            is_loaded = cfg.get('is_loaded', False)
            needs_retrofit = cfg.get('needs_retrofit', True)

            if is_loaded:
                # Reject loaded wagons - log rejection event
                if self.event_publisher:
                    self.event_publisher(
                        WagonJourneyEvent(
                            timestamp=arrival_time,
                            wagon_id=cfg['id'],
                            event_type='REJECTED',
                            location='collection',
                            status='REJECTED_LOADED',
                            train_id=train_id,
                            rejection_reason='Loaded',
                            rejection_description='Wagon is loaded',
                        )
                    )
            elif not needs_retrofit:
                # Reject wagons that don't need retrofit - log rejection event
                if self.event_publisher:
                    self.event_publisher(
                        WagonJourneyEvent(
                            timestamp=arrival_time,
                            wagon_id=cfg['id'],
                            event_type='REJECTED',
                            location='collection',
                            status='REJECTED_NO_RETROFIT_NEEDED',
                            train_id=train_id,
                            rejection_reason='No Retrofit Needed',
                            rejection_description="Wagon doesn't need retrofit",
                        )
                    )
            else:
                eligible_configs.append(cfg)

        # Create wagons only for eligible ones
        wagons = [
            Wagon(
                id=cfg['id'],
                length=cfg.get('length', 15.0),
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
            for cfg in eligible_configs
        ]

        # Create train aggregate (owns wagons during arrival)
        train = Train(
            id=train_id,
            arrival_time=arrival_time,
            wagons=wagons,
        )

        self.trains.append(train)

        # Schedule arrival process
        self.env.process(self._process_arrival(train, arrival_time))

    def _process_arrival(
        self,
        train: Train,
        arrival_time: float,
    ) -> Generator[Any, Any]:
        """Process a single train arrival through the complete arrival workflow.

        Handles the complete arrival process including timing coordination,
        classification operations, event publishing, and wagon placement
        on collection tracks.

        Parameters
        ----------
        train : Train
            Train aggregate containing wagons to process
        arrival_time : float
            Scheduled arrival time in simulation ticks

        Yields
        ------
        Generator[Any, Any, None]
            SimPy process generator for simulation execution

        Notes
        -----
        The arrival process follows these steps:
        1. Wait until the scheduled arrival time
        2. Start train classification process
        3. Publish arrival events for each wagon
        4. Complete classification and transfer wagon ownership
        5. Place classified wagons on collection queue

        This method is private and called automatically by the SimPy
        process scheduler when trains are scheduled.

        Examples
        --------
        This method is called internally by schedule_train() and should
        not be invoked directly by external code.
        """
        # Wait until arrival time
        if arrival_time > self.env.now:
            yield self.env.timeout(arrival_time - self.env.now)

        # Train arrives - start classification
        train.start_classification(self.env.now)

        # Publish ARRIVED events for each wagon
        for wagon in train.wagons:
            if self.event_publisher:
                self.event_publisher(
                    WagonJourneyEvent(
                        timestamp=self.env.now,
                        wagon_id=wagon.id,
                        event_type='ARRIVED',
                        location='collection',
                        status='ARRIVED',
                        train_id=train.id,
                    )
                )

        # Complete classification - transfers ownership and classifies wagons
        classified_wagons = train.complete_classification()

        # Put wagons on collection track (FIFO queue)
        for wagon in classified_wagons:
            self.collection_queue.put(wagon)
