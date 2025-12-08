"""Event count value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventCount:
    """Count of events with type."""

    event_type: str
    count: int

    def __post_init__(self) -> None:
        if self.count < 0:
            msg = "Event count cannot be negative"
            raise ValueError(msg)
        if not self.event_type or not self.event_type.strip():
            msg = "Event type cannot be empty"
            raise ValueError(msg)

    def increment(self) -> "EventCount":
        """Create new EventCount with incremented value."""
        return EventCount(self.event_type, self.count + 1)

    def add(self, amount: int) -> "EventCount":
        """Create new EventCount with added amount."""
        if amount < 0:
            msg = "Cannot add negative amount"
            raise ValueError(msg)
        return EventCount(self.event_type, self.count + amount)
