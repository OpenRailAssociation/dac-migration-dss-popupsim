"""Concrete resource trackers for different resource types."""

from shared.domain.resource_status import (
    LocoStatus,
    TrackStatus,
    WagonStatus,
    WorkshopStatus,
)
from shared.infrastructure.resource_tracker import ResourceTracker


class LocomotiveTracker(ResourceTracker[LocoStatus]):
    """Tracks locomotive status changes."""


class WagonTracker(ResourceTracker[WagonStatus]):
    """Tracks wagon status changes."""


class WorkshopTracker(ResourceTracker[WorkshopStatus]):
    """Tracks workshop status changes."""


class TrackTracker(ResourceTracker[TrackStatus]):
    """Tracks track status changes."""
