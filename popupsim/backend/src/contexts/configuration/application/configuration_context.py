"""Configuration Context - Step-by-step static configuration management."""

from typing import Any

from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from contexts.configuration.domain.models import ConfigurationState
from contexts.configuration.domain.models import LocomotiveConfig
from contexts.configuration.domain.models import ProcessTimesConfig
from contexts.configuration.domain.models import ScenarioMetadata
from contexts.configuration.domain.models import StrategiesConfig
from contexts.configuration.domain.models import TopologyConfig
from contexts.configuration.domain.models import TrackConfig
from contexts.configuration.domain.models import WorkshopConfig
from infrastructure.event_bus.event_bus import EventBus
from shared.domain.events.configuration_events import ConfigurationLoadedEvent
from shared.validation.base import ValidationIssue
from shared.validation.base import ValidationLevel
from shared.validation.base import ValidationResult


class ConfigurationContext:
    """Configuration Context managing step-by-step static configuration.

    Following ADR-002: Handles only static configuration (workshop layout, process times, topology).
    Dynamic external data (trains) moved to External Trains Context.
    Supports API-driven step-by-step configuration building.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._builders: dict[str, ConfigurationBuilder] = {}
        self._finalized_scenarios: dict[str, Any] = {}

    def create_scenario(self, metadata: ScenarioMetadata) -> ValidationResult:
        """Create new scenario configuration."""
        if metadata.id in self._builders:
            issue = ValidationIssue(message=f'Scenario {metadata.id} already exists', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        self._builders[metadata.id] = ConfigurationBuilder(metadata)
        return ValidationResult(is_valid=True, issues=[])

    def add_workshop(self, scenario_id: str, workshop: WorkshopConfig) -> ValidationResult:
        """Add workshop to scenario configuration."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.add_workshop(workshop)

    def add_track(self, scenario_id: str, track: TrackConfig) -> ValidationResult:
        """Add track to scenario configuration."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.add_track(track)

    def add_locomotive(self, scenario_id: str, locomotive: LocomotiveConfig) -> ValidationResult:
        """Add locomotive to scenario configuration."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.add_locomotive(locomotive)

    def set_process_times(self, scenario_id: str, times: ProcessTimesConfig) -> ValidationResult:
        """Set process times for scenario."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.set_process_times(times)

    def set_topology(self, scenario_id: str, topology: TopologyConfig) -> ValidationResult:
        """Set topology for scenario."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.set_topology(topology)

    def set_strategies(self, scenario_id: str, strategies: StrategiesConfig) -> ValidationResult:
        """Set selection strategies for scenario."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.set_strategies(strategies)

    def get_configuration_state(self, scenario_id: str) -> ConfigurationState | None:
        """Get current configuration state."""
        builder = self._builders.get(scenario_id)
        return builder.get_configuration_state() if builder else None

    def validate_scenario(self, scenario_id: str) -> ValidationResult:
        """Validate scenario configuration."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return ValidationResult(is_valid=False, issues=[issue])

        return builder.validate_completeness()

    def finalize_scenario(self, scenario_id: str) -> tuple[Any, ValidationResult]:
        """Finalize scenario configuration."""
        builder = self._builders.get(scenario_id)
        if not builder:
            issue = ValidationIssue(message=f'Scenario {scenario_id} not found', level=ValidationLevel.WARNING)
            return None, ValidationResult(is_valid=False, issues=[issue])

        validation = builder.validate_completeness()
        if not validation.is_valid:
            return None, validation

        scenario = builder.build_scenario()
        self._finalized_scenarios[scenario_id] = scenario

        # Publish configuration loaded event
        event = ConfigurationLoadedEvent(scenario=scenario)
        self.event_bus.publish(event)

        return scenario, ValidationResult(is_valid=True, issues=[])

    def get_scenario(self, scenario_id: str) -> Any | None:
        """Get finalized scenario."""
        return self._finalized_scenarios.get(scenario_id)

    def delete_scenario(self, scenario_id: str) -> ValidationResult:
        """Delete scenario configuration."""
        if scenario_id in self._builders:
            del self._builders[scenario_id]
        if scenario_id in self._finalized_scenarios:
            del self._finalized_scenarios[scenario_id]
        return ValidationResult(is_valid=True, issues=[])

    def initialize(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize context (no-op for configuration)."""

    def start_processes(self) -> None:
        """Start processes (no-op for configuration)."""

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics."""
        return {'scenarios': len(self._finalized_scenarios)}

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {'status': 'ready'}

    def cleanup(self) -> None:
        """Cleanup (no-op)."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
