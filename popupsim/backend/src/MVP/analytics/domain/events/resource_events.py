"""Resource allocation events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class ResourceAllocatedEvent(DomainEvent):
    """Event when resource is allocated."""

    _context = "shunting_operations"

    resource_id: str
    resource_type: str  # 'locomotive', 'workshop_station', 'track'
    allocated_to: str


@dataclass(frozen=True)
class ResourceReleasedEvent(DomainEvent):
    """Event when resource is released."""

    _context = "shunting_operations"

    resource_id: str
    resource_type: str
    released_from: str
