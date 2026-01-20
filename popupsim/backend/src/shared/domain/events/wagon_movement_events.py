"""Wagon movement events for track occupancy synchronization."""

from dataclasses import dataclass


@dataclass
class WagonMovedEvent:
    """Event published when a wagon is moved between tracks."""

    wagon_id: str
    from_track: str | None
    to_track: str
    timestamp: float
    movement_type: str = 'shunting'  # 'shunting', 'classification', 'manual'
