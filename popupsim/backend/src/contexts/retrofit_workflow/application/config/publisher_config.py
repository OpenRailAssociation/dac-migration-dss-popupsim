"""Publisher configuration for retrofit workflows context."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class PublisherConfig:
    """Configuration for event publishers."""

    wagon_event_publisher: Callable[[Any], None] | None = None
    locomotive_event_publisher: Callable[[Any], None] | None = None
    batch_event_publisher: Callable[[Any], None] | None = None

    def has_wagon_publisher(self) -> bool:
        """Check if wagon event publisher is configured."""
        return self.wagon_event_publisher is not None

    def has_locomotive_publisher(self) -> bool:
        """Check if locomotive event publisher is configured."""
        return self.locomotive_event_publisher is not None

    def has_batch_publisher(self) -> bool:
        """Check if batch event publisher is configured."""
        return self.batch_event_publisher is not None

    def publish_wagon_event(self, event: Any) -> None:
        """Publish wagon event if publisher configured."""
        if self.wagon_event_publisher:
            self.wagon_event_publisher(event)

    def publish_locomotive_event(self, event: Any) -> None:
        """Publish locomotive event if publisher configured."""
        if self.locomotive_event_publisher:
            self.locomotive_event_publisher(event)

    def publish_batch_event(self, event: Any) -> None:
        """Publish batch event if publisher configured."""
        if self.batch_event_publisher:
            self.batch_event_publisher(event)
