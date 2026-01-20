"""Event publishing port for hexagonal architecture."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from ...domain.events.batch_events import DomainEvent


class EventPublishingPort(ABC):
    """Port for publishing domain events."""

    @abstractmethod
    def publish_event(self, event: DomainEvent) -> Generator[Any, Any]:
        """Publish domain event."""
        pass

    @abstractmethod
    def publish_events(self, events: list[DomainEvent]) -> Generator[Any, Any]:
        """Publish multiple domain events."""
        pass
