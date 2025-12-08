"""Locomotive movement and status events."""

from dataclasses import dataclass


@dataclass
class LocomotiveMovementStartedEvent:
    """Locomotive started moving between tracks."""

    locomotive_id: str
    from_track: str
    to_track: str
    event_timestamp: float = 0.0


@dataclass
class LocomotiveMovementCompletedEvent:
    """Locomotive completed movement between tracks."""

    locomotive_id: str
    from_track: str
    to_track: str
    event_timestamp: float = 0.0


@dataclass
class WagonLocationChangedEvent:
    """Wagon location changed to new track."""

    wagon_id: str
    track: str
    event_timestamp: float = 0.0
