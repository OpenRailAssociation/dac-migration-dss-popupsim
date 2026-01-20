"""Helper for publishing coordinator events - eliminates duplicate code."""

from collections.abc import Callable

from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent


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
