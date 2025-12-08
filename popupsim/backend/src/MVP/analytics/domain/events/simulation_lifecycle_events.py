"""Simulation lifecycle events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class SimulationStartedEvent(DomainEvent):
    """Event when simulation starts."""

    _context = "simulation"

    scenario_id: str
    expected_duration_minutes: float


@dataclass(frozen=True)
class SimulationEndedEvent(DomainEvent):
    """Event when simulation ends."""

    _context = "simulation"

    scenario_id: str
    completion_status: str  # 'completed', 'terminated', 'error'
