"""Retrofit process events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class RetrofitStartedEvent(DomainEvent):
    """Event when wagon retrofit starts."""

    _context = 'popup_retrofit'

    wagon_id: str
    workshop_id: str
    station_id: str


@dataclass(frozen=True)
class RetrofitCompletedEvent(DomainEvent):
    """Event when wagon retrofit completes."""

    _context = 'popup_retrofit'

    wagon_id: str
    workshop_id: str
    station_id: str
    success: bool
