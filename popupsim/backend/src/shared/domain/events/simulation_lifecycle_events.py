"""Simulation lifecycle events."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from infrastructure.events.base_event import DomainEvent


@dataclass(frozen=True)
class SimulationStartedEvent(DomainEvent):
    """Event fired when simulation starts."""

    scenario_id: str = ''
    expected_duration: float = 0.0
    contexts_count: int = 0

    @classmethod
    def create(cls, scenario_id: str, expected_duration: float, contexts_count: int) -> 'SimulationStartedEvent':
        """Create simulation started event."""
        return cls(
            scenario_id=scenario_id,
            expected_duration=expected_duration,
            contexts_count=contexts_count,
        )


@dataclass(frozen=True)
class SimulationEndedEvent(DomainEvent):
    """Event fired when simulation ends successfully."""

    scenario_id: str = ''
    actual_duration: float = 0.0
    completion_status: str = 'completed'
    final_metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        scenario_id: str,
        actual_duration: float,
        completion_status: str = 'completed',
        final_metrics: dict[str, Any] | None = None,
    ) -> 'SimulationEndedEvent':
        """Create simulation ended event."""
        return cls(
            scenario_id=scenario_id,
            actual_duration=actual_duration,
            completion_status=completion_status,
            final_metrics=final_metrics or {},
        )


@dataclass(frozen=True)
class SimulationFailedEvent(DomainEvent):
    """Event fired when simulation fails."""

    scenario_id: str = ''
    error_message: str = ''
    failure_time: float = 0.0
    context_states: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        scenario_id: str,
        error_message: str,
        failure_time: float,
        context_states: dict[str, str] | None = None,
    ) -> 'SimulationFailedEvent':
        """Create simulation failed event."""
        return cls(
            scenario_id=scenario_id,
            error_message=error_message,
            failure_time=failure_time,
            context_states=context_states or {},
        )


@dataclass(frozen=True)
class ContextInitializedEvent(DomainEvent):
    """Event fired when a context is initialized."""

    context_name: str = ''
    context_type: str = ''
    initialization_time: float = 0.0

    @classmethod
    def create(cls, context_name: str, context_type: str, initialization_time: float) -> 'ContextInitializedEvent':
        """Create context initialized event."""
        return cls(
            context_name=context_name,
            context_type=context_type,
            initialization_time=initialization_time,
        )


@dataclass(frozen=True)
class ContextStartedEvent(DomainEvent):
    """Event fired when a context starts its processes."""

    context_name: str = ''
    processes_count: int = 0
    start_time: float = 0.0

    @classmethod
    def create(cls, context_name: str, processes_count: int, start_time: float) -> 'ContextStartedEvent':
        """Create context started event."""
        return cls(
            context_name=context_name,
            processes_count=processes_count,
            start_time=start_time,
        )
