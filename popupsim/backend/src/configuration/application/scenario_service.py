"""Hexagonal + Pipeline scenario service."""

from pathlib import Path

from shared.validation.base import ValidationResult

from configuration.application.pipeline.scenario_pipeline import ScenarioPipeline
from configuration.domain.models.scenario import Scenario
from configuration.domain.ports.scenario_port import ScenarioPort
from configuration.infrastructure.adapters.csv_scenario_adapter import CsvScenarioAdapter
from configuration.infrastructure.adapters.json_scenario_adapter import JsonScenarioAdapter


class ScenarioService:
    """Hexagonal architecture service with pipeline for loading scenarios."""

    def __init__(self, adapters: list[ScenarioPort] | None = None) -> None:
        """Initialize with scenario adapters."""
        self._adapters = adapters or [
            JsonScenarioAdapter(),
            CsvScenarioAdapter(),
        ]

    def load_scenario(self, source_path: str | Path) -> tuple[Scenario | None, ValidationResult]:
        """Load scenario using hexagonal architecture with pipeline."""
        source = Path(source_path)
        adapter = self._get_adapter(source)
        pipeline = ScenarioPipeline(adapter)
        return pipeline.process(source)

    def register_adapter(self, adapter: ScenarioPort) -> None:
        """Register new adapter."""
        self._adapters.append(adapter)

    def _get_adapter(self, source: Path) -> ScenarioPort:
        """Get appropriate adapter for source."""
        for adapter in self._adapters:
            if adapter.supports(source):
                return adapter
        raise ValueError(f'No adapter supports source: {source}')
