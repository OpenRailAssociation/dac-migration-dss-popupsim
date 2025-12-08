"""Base domain event."""

from abc import ABC
from dataclasses import dataclass
from typing import Any

from MVP.analytics.domain.value_objects.event_id import EventId
from MVP.analytics.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""

    event_id: EventId
    timestamp: Timestamp
    context: str

    @classmethod
    def create(cls, timestamp: Timestamp, **kwargs: Any) -> "DomainEvent":
        """Create event with generated ID and auto-derived context."""
        context = getattr(cls, "_context", cls.__module__.split(".", maxsplit=1)[0])
        return cls(
            event_id=EventId.generate(), timestamp=timestamp, context=context, **kwargs
        )
