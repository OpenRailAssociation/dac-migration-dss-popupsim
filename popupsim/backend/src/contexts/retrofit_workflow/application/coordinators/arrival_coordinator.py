"""Arrival coordinator for managing train arrivals and wagon processing.

Refactored version with improved separation of concerns:
- Pure coordination logic (no domain business rules)
- Minimal dependencies
- Clear single responsibility
- Proper error handling
"""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import ArrivalCoordinatorConfig
from contexts.retrofit_workflow.application.coordinators.base_coordinator import BaseCoordinator
from contexts.retrofit_workflow.domain.aggregates.train_aggregate import Train
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.services.rejection_event_factory import RejectionEventFactory
from contexts.retrofit_workflow.domain.services.wagon_eligibility_service import EligibilityResult
from contexts.retrofit_workflow.domain.services.wagon_eligibility_service import WagonEligibilityService
from contexts.retrofit_workflow.domain.services.wagon_factory_service import WagonFactoryService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType


class ArrivalCoordinator(BaseCoordinator):
    """Coordinator for managing train arrivals and initial wagon processing.

    Responsibilities:
    - Schedule train arrivals
    - Create wagon entities from configuration
    - Coordinate with collection system
    - Publish arrival events

    Does NOT handle:
    - Business rules for wagon filtering (delegated to domain service)
    - Track selection logic (delegated to track selector)
    - Collection queue management (delegated to collection coordinator)
    """

    def __init__(self, config: ArrivalCoordinatorConfig) -> None:
        """Initialize arrival coordinator.

        Args:
            config: Configuration with all required dependencies
        """
        super().__init__(config.env)
        self._collection_queue = config.collection_queue
        self._track_selector = config.track_selector
        self._collection_coordinator = config.collection_coordinator
        self._event_publisher = config.event_publisher
        self._track_manager = config.track_manager  # Add track manager for capacity management
        self._wagon_factory = WagonFactoryService()
        self._eligibility_service = WagonEligibilityService()
        self._rejection_factory = RejectionEventFactory()
        self._trains: list[Train] = []

    def schedule_train(
        self,
        train_id: str,
        arrival_time: float,
        wagon_configs: list[dict[str, Any]],
    ) -> None:
        """Schedule a train arrival.

        Args:
            train_id: Unique train identifier
            arrival_time: When train should arrive (simulation time)
            wagon_configs: List of wagon configuration dictionaries
        """
        # Create wagons using domain service
        wagons = self._create_wagons_from_configs(wagon_configs, train_id, arrival_time)

        if not wagons:
            raise ValueError(f'Train {train_id} must have at least one wagon')

        # Create train aggregate
        train = Train(
            id=train_id,
            arrival_time=arrival_time,
            wagons=wagons,
        )

        self._trains.append(train)

        # Schedule arrival process
        self.env.process(self._process_arrival(train))

    def start(self) -> None:
        """Start arrival coordinator.

        Note: Arrival coordinator is event-driven and doesn't need
        continuous processes. Trains are scheduled via schedule_train().
        """

    def get_trains(self) -> list[Train]:
        """Get all scheduled trains.

        Returns
        -------
            List of train aggregates
        """
        return self._trains.copy()

    def _create_wagons_from_configs(
        self, wagon_configs: list[dict[str, Any]], train_id: str, arrival_time: float
    ) -> list[Wagon]:
        """Create wagon entities from configuration data.

        Args:
            wagon_configs: Wagon configuration dictionaries
            train_id: Train identifier for event publishing
            arrival_time: Arrival time for event publishing

        Returns
        -------
            List of eligible wagon entities
        """
        eligible_wagons = []

        for config in wagon_configs:
            # Check eligibility using domain service
            eligibility_result = self._eligibility_service.is_eligible_for_retrofit(config)

            if not eligibility_result.is_eligible:
                self._publish_rejection_event(config, eligibility_result, train_id, arrival_time)
                continue

            # Create wagon entity
            wagon = self._wagon_factory.create_wagon(
                wagon_id=config['id'],
                length=config.get('length', 15.0),
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )

            # Set train_id for rejection tracking
            wagon.train_id = train_id

            eligible_wagons.append(wagon)

        return eligible_wagons

    def _publish_rejection_event(
        self, config: dict[str, Any], eligibility_result: EligibilityResult, train_id: str, arrival_time: float
    ) -> None:
        """Publish rejection event for ineligible wagon.

        Args:
            config: Wagon configuration
            eligibility_result: Result from eligibility check
            train_id: Train identifier
            arrival_time: Arrival time
        """
        if not self._event_publisher:
            return

        rejection_event = self._rejection_factory.create_rejection_event(
            config, eligibility_result, train_id, arrival_time
        )
        # Override location to 'REJECTED' since wagon never gets on a track
        rejection_event = WagonJourneyEvent(
            timestamp=rejection_event.timestamp,
            wagon_id=rejection_event.wagon_id,
            event_type=rejection_event.event_type,
            location='REJECTED',
            status=rejection_event.status,
            train_id=rejection_event.train_id,
            rejection_reason=rejection_event.rejection_reason,
            rejection_description=rejection_event.rejection_description,
        )
        self._event_publisher(rejection_event)

    def _process_arrival(self, train: Train) -> Generator[Any, Any]:
        """Process train arrival through complete workflow.

        Args:
            train: Train aggregate to process

        Yields
        ------
            SimPy process events
        """
        # Wait until arrival time
        if train.arrival_time > self.env.now:
            yield self.env.timeout(train.arrival_time - self.env.now)

        # Start classification
        train.start_classification(self.env.now)

        # Complete classification and get wagons
        classified_wagons = train.complete_classification()

        # Distribute wagons to collection tracks with capacity reservation
        yield from self._distribute_wagons_to_collection_async(classified_wagons)

        # Publish arrival events AFTER track assignment
        self._publish_arrival_events(train)

    def _publish_arrival_events(self, train: Train) -> None:
        """Publish arrival events for all wagons in train.

        Args:
            train: Train aggregate
        """
        if not self._event_publisher:
            return

        for wagon in train.wagons:
            # Use actual track ID if assigned, otherwise 'collection'
            location = wagon.current_track_id if wagon.current_track_id else 'collection'
            self._event_publisher(
                WagonJourneyEvent(
                    timestamp=self.env.now,
                    wagon_id=wagon.id,
                    event_type='ARRIVED',
                    location=location,
                    status='ARRIVED',
                    train_id=train.id,
                )
            )

    def _distribute_wagons_to_collection(self, wagons: list[Wagon]) -> None:
        """Distribute wagons to collection tracks with capacity management.

        Args:
            wagons: List of classified wagons
        """
        for wagon in wagons:
            # Select collection track
            collection_track = self._track_selector.select_track_with_capacity('collection')
            if not collection_track:
                continue  # Skip if no track available

            # Assign wagon to track
            wagon.current_track_id = collection_track.track_id

            # Add to collection system
            self._collection_coordinator.add_wagon(wagon)

    def _distribute_wagons_to_collection_async(self, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Distribute wagons to collection tracks with capacity reservation (async version).

        Args:
            wagons: List of classified wagons

        Yields
        ------
            SimPy events for capacity reservation
        """
        for wagon in wagons:
            # Select collection track
            collection_track = self._track_selector.select_track_with_capacity('collection')
            if not collection_track:
                # No collection track available - reject wagon
                self._reject_wagon_no_track(wagon)
                continue

            # Check if wagon fits on collection track
            if self._track_manager:
                track = self._track_manager.get_track(collection_track.track_id)
                if track:
                    available_capacity = track.get_available_capacity()
                    if wagon.length > available_capacity:
                        # Collection track full - reject wagon with detailed message
                        self._reject_wagon_track_full(wagon, collection_track.track_id, available_capacity)
                        continue

            # Assign wagon to track
            wagon.current_track_id = collection_track.track_id

            # Reserve capacity on collection track (should not block since we checked capacity)
            if self._track_manager:
                track = self._track_manager.get_track(collection_track.track_id)
                if track:
                    yield from track.add_wagons([wagon])

            # Add to collection system
            self._collection_coordinator.add_wagon(wagon)

    def _reject_wagon_no_track(self, wagon: Wagon) -> None:
        """Reject wagon when no collection track is available.

        Args:
            wagon: Wagon to reject
        """
        if not self._event_publisher:
            return

        self._event_publisher(
            WagonJourneyEvent(
                timestamp=self.env.now,
                wagon_id=wagon.id,
                event_type='REJECTED',
                location='REJECTED',
                status='REJECTED',
                train_id=wagon.train_id if hasattr(wagon, 'train_id') else '',
                rejection_reason='NO_COLLECTION_TRACK',
                rejection_description='No collection track available',
            )
        )

    def _reject_wagon_track_full(self, wagon: Wagon, track_id: str, available_capacity: float) -> None:
        """Reject wagon when collection track is full.

        Args:
            wagon: Wagon to reject
            track_id: ID of the full collection track
            available_capacity: Available capacity on the track
        """
        if not self._event_publisher:
            return

        self._event_publisher(
            WagonJourneyEvent(
                timestamp=self.env.now,
                wagon_id=wagon.id,
                event_type='REJECTED',
                location='REJECTED',
                status='REJECTED',
                train_id=wagon.train_id if hasattr(wagon, 'train_id') else '',
                rejection_reason='COLLECTION_TRACK_FULL',
                rejection_description=f'Collection track {track_id} capacity exceeded '
                f'({available_capacity:.1f} meters available, {wagon.length:.1f} meters needed)',
            )
        )
