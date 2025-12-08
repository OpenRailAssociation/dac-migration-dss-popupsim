"""Locomotive-related domain events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class LocomotiveStatusChangeEvent(DomainEvent):
    """Event when locomotive status changes."""

    locomotive_id: str
    status: str


@dataclass(frozen=True)
class LocomotiveAssignedEvent(DomainEvent):
    """Event when locomotive is assigned to task."""

    locomotive_id: str
    task_id: str


@dataclass(frozen=True)
class LocomotiveIdleEvent(DomainEvent):
    """Event when locomotive becomes idle."""

    locomotive_id: str
