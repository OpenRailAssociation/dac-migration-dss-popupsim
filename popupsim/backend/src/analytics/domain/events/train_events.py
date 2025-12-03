"""Train operation events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class TrainArrivedEvent(DomainEvent):
    """Event when train arrives."""

    _context = 'external_trains'

    train_id: str
    track_id: str
    wagon_count: int


@dataclass(frozen=True)
class TrainDepartedEvent(DomainEvent):
    """Event when train departs."""

    _context = 'external_trains'

    train_id: str
    track_id: str
    wagon_count: int
