"""Helper for publishing coordinator events - eliminates duplicate code."""

from collections.abc import Callable
from typing import Any

from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted


class EventPublisherHelper:
    """Centralized event publishing to eliminate duplicate code across coordinators."""

    @staticmethod
    def publish_loco_allocated(
        publisher: Callable[[LocomotiveMovementEvent], None] | None,
        timestamp: float,
        loco_id: str,
        purpose: str = 'batch_transport',
    ) -> None:
        """Publish locomotive allocation event."""
        if publisher:
            publisher(
                LocomotiveMovementEvent(
                    timestamp=timestamp,
                    locomotive_id=loco_id,
                    event_type='ALLOCATED',
                    from_location=None,
                    to_location=None,
                    purpose=purpose,
                )
            )

    @staticmethod
    def publish_loco_moving(
        publisher: Callable[[LocomotiveMovementEvent], None] | None,
        timestamp: float,
        loco_id: str,
        from_location: str,
        to_location: str,
    ) -> None:
        """Publish locomotive movement event."""
        if publisher:
            publisher(
                LocomotiveMovementEvent(
                    timestamp=timestamp,
                    locomotive_id=loco_id,
                    event_type='MOVING',
                    from_location=from_location,
                    to_location=to_location,
                )
            )

    @staticmethod
    def publish_wagon_event(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
        publisher: Callable[[WagonJourneyEvent], None] | None,
        timestamp: float,
        wagon_id: str,
        event_type: str,
        location: str,
        status: str,
    ) -> None:
        """Publish wagon journey event."""
        if publisher:
            publisher(
                WagonJourneyEvent(
                    timestamp=timestamp,
                    wagon_id=wagon_id,
                    event_type=event_type,
                    location=location,
                    status=status,
                )
            )

    @staticmethod
    def publish_batch_formed(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
        publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None,
        timestamp: float,
        batch_id: str,
        wagon_ids: list[str],
        destination: str,
        total_length: float,
    ) -> None:
        """Publish batch formed event."""
        if publisher:
            publisher(
                BatchFormed(
                    timestamp=timestamp,
                    event_id=f'batch_formed_{batch_id}',
                    batch_id=batch_id,
                    wagon_ids=wagon_ids,
                    destination=destination,
                    total_length=total_length,
                )
            )

    @staticmethod
    def publish_batch_transport_started(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
        publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None,
        timestamp: float,
        batch_id: str,
        locomotive_id: str,
        destination: str,
        wagon_count: int,
    ) -> None:
        """Publish batch transport started event."""
        if publisher:
            publisher(
                BatchTransportStarted(
                    timestamp=timestamp,
                    event_id=f'batch_transport_{batch_id}',
                    batch_id=batch_id,
                    locomotive_id=locomotive_id,
                    destination=destination,
                    wagon_count=wagon_count,
                )
            )

    @staticmethod
    def publish_batch_arrived(
        publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None,
        timestamp: float,
        batch_id: str,
        destination: str,
        wagon_count: int,
    ) -> None:
        """Publish batch arrived at destination event."""
        if publisher:
            publisher(
                BatchArrivedAtDestination(
                    timestamp=timestamp,
                    event_id=f'batch_arrived_{batch_id}',
                    batch_id=batch_id,
                    destination=destination,
                    wagon_count=wagon_count,
                )
            )

    @staticmethod
    def publish_batch_events_for_aggregate(
        publisher: Callable[[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination], None] | None,
        timestamp: float,
        batch_aggregate: Any,
        destination: str,
    ) -> None:
        """Publish batch formed event from batch aggregate."""
        if publisher:
            batch_id = batch_aggregate.id
            wagons = batch_aggregate.wagons
            publisher(
                BatchFormed(
                    timestamp=timestamp,
                    event_id=f'batch_formed_{batch_id}',
                    batch_id=batch_id,
                    wagon_ids=[w.id for w in wagons],
                    destination=destination,
                    total_length=sum(w.length for w in wagons),
                )
            )
