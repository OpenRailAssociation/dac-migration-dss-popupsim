"""Scenario loading pipeline with validation and transformation stages."""

from pathlib import Path

from shared.validation.base import ValidationResult
from shared.validation.coordinator import ValidationCoordinator

from configuration.domain.factories.scenario_factory import ScenarioFactory
from configuration.domain.models.scenario import Scenario
from configuration.domain.ports.scenario_port import ScenarioPort


class ScenarioPipeline:
    """Pipeline for loading and processing scenarios with late validation."""

    def __init__(self, adapter: ScenarioPort) -> None:
        """Initialize pipeline with adapter."""
        self.adapter = adapter
        self.validation_coordinator = ValidationCoordinator()

    def process(self, source: Path) -> tuple[Scenario | None, ValidationResult]:
        """Process scenario through loading pipeline with late validation."""
        # Stage 1: Source validation only
        validation_result = self._validate_source(source)
        if not validation_result.is_valid:
            return None, validation_result

        # Stage 2: Load raw data (no validation)
        try:
            dto = self.adapter.load_scenario_dto(source)
            scenario = ScenarioFactory.from_dto(dto)
        except Exception as e:
            validation_result.add_error(f'Loading failed: {e}')
            return None, validation_result

        # Stage 3: Context validation (collect all issues)
        context_validation = self.validation_coordinator.validate_all(scenario)
        validation_result.merge(context_validation)

        return scenario, validation_result

    def _validate_source(self, source: Path) -> ValidationResult:
        """Validate source path and format."""
        result = ValidationResult(is_valid=True)

        if not source.exists():
            result.add_error(f'Source not found: {source}')
            return result

        if not self.adapter.supports(source):
            result.add_error(f'Unsupported source format: {source}')
            return result

        return result
