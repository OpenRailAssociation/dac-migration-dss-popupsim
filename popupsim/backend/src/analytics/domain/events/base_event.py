"""Base domain event."""

from abc import ABC
from dataclasses import dataclass
from typing import Any

from ..value_objects.event_id import EventId
from ..value_objects.timestamp import Timestamp


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""
    
    event_id: EventId
    timestamp: Timestamp
    
    @classmethod
    def create(cls, timestamp: Timestamp, **kwargs: Any) -> 'DomainEvent':
        """Create event with generated ID."""
        return cls(
            event_id=EventId.generate(),
            timestamp=timestamp,
            **kwargs
        )