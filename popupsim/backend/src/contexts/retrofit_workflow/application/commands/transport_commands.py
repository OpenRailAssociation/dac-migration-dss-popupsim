"""Transport commands following Command pattern."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.config.transport_config import EventPublishers
from contexts.retrofit_workflow.application.config.transport_config import TransportConfig
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.value_objects.batch_context import BatchContext
import simpy


class TransportCommand(ABC):  # pylint: disable=too-few-public-methods
    """Abstract command for transport operations."""

    @abstractmethod
    def execute(self) -> Generator[Any, Any]:
        """Execute the transport command."""


class BatchToWorkshopTransport(TransportCommand):  # pylint: disable=too-few-public-methods
    """Command to transport batch from retrofit track to workshop."""

    def __init__(
        self,
        transport_config: TransportConfig,
        batch_context: BatchContext,
        event_publishers: EventPublishers,
    ) -> None:
        """Initialize transport command.

        Parameters
        ----------
        transport_config : TransportConfig
            Core transport dependencies and configuration
        batch_context : BatchContext
            Batch information and context
        event_publishers : EventPublishers
            Event publishing configuration
        """
        self.config = transport_config
        self.batch_context = batch_context
        self.publishers = event_publishers

    def execute(self) -> Generator[Any, Any]:  # noqa: C901
        """Execute batch transport to workshop."""
        # Allocate locomotive
        loco = yield from self.config.locomotive_manager.allocate()
        self.batch_context.locomotive = loco

        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='ALLOCATED',
                    purpose='transport_to_workshop',
                    current_location=loco.home_track,
                )
            )

        # Move to retrofit track
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='MOVING',
                    from_location=loco.home_track,
                    to_location='retrofit',
                )
            )

        pickup_time = self.config.route_service.get_retrofit_to_workshop_time(self.batch_context.workshop_id)
        yield self.config.env.timeout(pickup_time)

        # Emit PARKING event after arrival at retrofit track
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='PARKING',
                    current_location='retrofit',
                )
            )

        # Emit COUPLING event before removing wagons
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='COUPLING',
                    current_location='retrofit',
                )
            )

        # Remove wagons from retrofit track
        retrofit_tracks = self.config.track_selector.get_tracks_of_type('retrofit')
        for track in retrofit_tracks:
            if track.can_fit_wagons(self.batch_context.wagons):
                yield from track.remove_wagons(self.batch_context.wagons)
                break

        # Transport to workshop
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='MOVING',
                    from_location='retrofit',
                    to_location=self.batch_context.workshop_id,
                )
            )

        transport_time = self.config.route_service.get_retrofit_to_workshop_time(self.batch_context.workshop_id)
        yield self.config.env.timeout(transport_time)

        # Emit PARKING event after arrival at workshop
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='PARKING',
                    current_location=self.batch_context.workshop_id,
                )
            )

        # Emit DECOUPLING event
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='DECOUPLING',
                    current_location=self.batch_context.workshop_id,
                )
            )

        # Publish arrival events
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='ARRIVED',
                    current_location=self.batch_context.workshop_id,
                )
            )

        for wagon in self.batch_context.wagons:
            if self.publishers.wagon_event_publisher:
                self.publishers.wagon_event_publisher(
                    WagonJourneyEvent(
                        timestamp=self.config.env.now,
                        wagon_id=wagon.id,
                        event_type='AT_WORKSHOP',
                        location=self.batch_context.workshop_id,
                        status='READY',
                    )
                )


class BatchFromWorkshopTransport(TransportCommand):  # pylint: disable=too-few-public-methods
    """Command to transport batch from workshop to retrofitted track."""

    def __init__(
        self,
        transport_config: TransportConfig,
        batch_context: BatchContext,
        retrofitted_queue: simpy.FilterStore,
        event_publishers: EventPublishers,
    ) -> None:
        """Initialize transport command.

        Parameters
        ----------
        transport_config : TransportConfig
            Core transport dependencies and configuration
        batch_context : BatchContext
            Batch information and context
        retrofitted_queue : simpy.FilterStore
            Queue for retrofitted wagons
        event_publishers : EventPublishers
            Event publishing configuration
        """
        self.config = transport_config
        self.batch_context = batch_context
        self.retrofitted_queue = retrofitted_queue
        self.publishers = event_publishers

    def execute(self) -> Generator[Any, Any]:  # noqa: C901
        """Execute batch transport from workshop to retrofitted track."""
        # Allocate locomotive for pickup
        loco = yield from self.config.locomotive_manager.allocate()

        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='ALLOCATED',
                    purpose='pickup_from_workshop',
                )
            )

        # Move to workshop
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='MOVING',
                    from_location=loco.home_track,
                    to_location=self.batch_context.workshop_id,
                )
            )

        pickup_time = self.config.route_service.get_retrofit_to_workshop_time(self.batch_context.workshop_id)
        yield self.config.env.timeout(pickup_time)

        # Emit PARKING event after arrival at workshop
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='PARKING',
                    current_location=self.batch_context.workshop_id,
                )
            )

        # Emit COUPLING event before picking up wagons
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='COUPLING',
                    current_location=self.batch_context.workshop_id,
                )
            )

        # Transport to retrofitted track
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='MOVING',
                    from_location=self.batch_context.workshop_id,
                    to_location='retrofitted',
                )
            )

        transport_time = self.config.route_service.get_workshop_to_retrofitted_time(self.batch_context.workshop_id)
        yield self.config.env.timeout(transport_time)

        # Emit PARKING event after arrival at retrofitted track
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='PARKING',
                    current_location='retrofitted',
                )
            )

        # Emit DECOUPLING event
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='DECOUPLING',
                    current_location='retrofitted',
                )
            )

        # Add to retrofitted track
        retrofitted_tracks = self.config.track_selector.get_tracks_of_type('retrofitted')
        if retrofitted_tracks:
            retrofitted_track = retrofitted_tracks[0]
            yield from retrofitted_track.add_wagons(self.batch_context.wagons)

        # Put wagons on retrofitted queue and publish events
        for wagon in self.batch_context.wagons:
            yield self.retrofitted_queue.put(wagon)

            if self.publishers.wagon_event_publisher:
                self.publishers.wagon_event_publisher(
                    WagonJourneyEvent(
                        timestamp=self.config.env.now,
                        wagon_id=wagon.id,
                        event_type='ON_RETROFITTED_TRACK',
                        location='retrofitted',
                        status='WAITING',
                    )
                )

        # Return locomotive
        return_time = self.config.route_service.get_workshop_to_retrofitted_time(self.batch_context.workshop_id)
        yield self.config.env.timeout(return_time)

        yield from self.config.locomotive_manager.release(loco)

        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=loco.id,
                    event_type='RELEASED',
                )
            )


class LocomotiveReturnCommand(TransportCommand):  # pylint: disable=too-few-public-methods
    """Command to return locomotive to home in parallel with other operations."""

    def __init__(
        self,
        transport_config: TransportConfig,
        locomotive: Any,
        return_time: float,
        event_publishers: EventPublishers,
    ) -> None:
        """Initialize return command.

        Parameters
        ----------
        transport_config : TransportConfig
            Core transport dependencies and configuration
        locomotive : Any
            Locomotive to return
        return_time : float
            Time for return journey
        event_publishers : EventPublishers
            Event publishing configuration
        """
        self.config = transport_config
        self.locomotive = locomotive
        self.return_time = return_time
        self.publishers = event_publishers

    def execute(self) -> Generator[Any, Any]:
        """Execute locomotive return."""
        if self.publishers.loco_event_publisher:
            self.publishers.loco_event_publisher(
                LocomotiveMovementEvent(
                    timestamp=self.config.env.now,
                    locomotive_id=self.locomotive.id,
                    event_type='MOVING',
                    to_location=self.locomotive.home_track,
                )
            )

        yield self.config.env.timeout(self.return_time)
        yield from self.config.locomotive_manager.release(self.locomotive)
