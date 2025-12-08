"""Locomotive status tracking service."""

from shared.domain.resource_status import LocoStatus
from shared.infrastructure.resource_tracker import ResourceTracker


class LocomotiveStatusTracker(ResourceTracker[LocoStatus]):
    """Tracks locomotive status changes via domain events."""
