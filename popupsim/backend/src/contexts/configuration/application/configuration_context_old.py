"""Configuration Context - Step-by-step static configuration management."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.event_bus.event_bus import EventBus
from MVP.configuration.domain.models.scenario import Scenario
from shared.validation.base import ValidationResult

if TYPE_CHECKING:
    from contexts.configuration.domain.configuration_builder import (
        ConfigurationBuilder,
    )


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

    def load_scenario(
        self, config_path: str | Path
    ) -> tuple[Scenario | None, ValidationResult]:
        """Load scenario configuration from file."""
        self._scenario, self._validation_result = self.scenario_service.load_scenario(
            config_path
        )

        if self._scenario:
            # Publish configuration loaded event
            from shared.domain.events.configuration_events import (
                ConfigurationLoadedEvent,
            )

            event = ConfigurationLoadedEvent(scenario=self._scenario)
            self.event_bus.publish(event)

        return self._scenario, self._validation_result

    def get_scenario(self) -> Scenario | None:
        """Get loaded scenario configuration."""
        return self._scenario

    def get_validation_result(self) -> ValidationResult | None:
        """Get last validation result."""
        return self._validation_result

    def get_workshop_config(self) -> list[Any]:
        """Get workshop configuration."""
        return self._scenario.workshops if self._scenario else []

    def get_process_times(self) -> Any:
        """Get process timing configuration."""
        return self._scenario.process_times if self._scenario else None

    def get_topology(self) -> Any:
        """Get topology configuration."""
        return self._scenario.topology if self._scenario else None

    def get_tracks(self) -> list[Any]:
        """Get track configuration."""
        return self._scenario.tracks if self._scenario else []

    def get_locomotives(self) -> list[Any]:
        """Get locomotive configuration."""
        return self._scenario.locomotives if self._scenario else []

    def get_routes(self) -> list[Any]:
        """Get route configuration."""
        return self._scenario.routes if self._scenario else []

    def get_metrics(self) -> dict[str, Any]:
        """Get configuration context metrics."""
        return {
            "scenario_loaded": self._scenario is not None,
            "validation_passed": self._validation_result.is_valid
            if self._validation_result
            else False,
            "workshops_count": len(self._scenario.workshops)
            if self._scenario and self._scenario.workshops
            else 0,
            "tracks_count": len(self._scenario.tracks)
            if self._scenario and self._scenario.tracks
            else 0,
            "locomotives_count": len(self._scenario.locomotives)
            if self._scenario and self._scenario.locomotives
            else 0,
        }
