"""Resource interfaces for retrofit workflow context."""

from collections.abc import Generator
from typing import Any
from typing import Protocol


class WorkshopResourceManager(Protocol):
    """Protocol for workshop resource management."""

    def request_bay(self, workshop_id: str) -> Generator[Any, Any, Any]:
        """Request bay at workshop."""

    def release_bay(self, workshop_id: str, request: Any) -> None:
        """Release bay at workshop."""

    def get_available_bays(self, workshop_id: str) -> int:
        """Get number of available bays."""


class TrackSelector(Protocol):
    """Protocol for track selection and capacity management."""

    def select_track_with_capacity(self, track_type: str, required_capacity: float = 0) -> Any:
        """Select track with available capacity."""

    def get_available_capacity(self, track_type: str) -> float:
        """Get total available capacity for track type."""


class EventPublisher(Protocol):
    """Protocol for event publishing."""

    def publish_wagon_event(self, event: Any) -> None:
        """Publish wagon-related event."""

    def publish_locomotive_event(self, event: Any) -> None:
        """Publish locomotive-related event."""

    def publish_batch_event(self, event: Any) -> None:
        """Publish batch-related event."""
