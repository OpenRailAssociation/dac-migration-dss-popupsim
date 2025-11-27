"""Validation coordinator using 4-layer pipeline."""

from shared.validation.base import ValidationResult
from shared.validation.pipeline import ValidationPipeline

from configuration.domain.models.scenario import Scenario


class ValidationCoordinator:
    """Coordinates validation using 4-layer pipeline with error stacking."""

    def __init__(self) -> None:
        """Initialize with validation pipeline and context validators."""
        self.pipeline = ValidationPipeline()
        self.context_validators: list = []  # Additional validators can be added

    def validate_all(self, scenario: Scenario) -> ValidationResult:
        """Validate scenario using 4-layer pipeline + context validators."""
        # Start with 4-layer pipeline (stacks all errors)
        result = self.pipeline.validate(scenario)

        # Add context-specific validation
        for validator in self.context_validators:
            context_result = validator.validate(scenario)
            result.merge(context_result)

        return result

    def add_validator(self, validator: object) -> None:
        """Add a new context validator."""
        if hasattr(validator, 'validate'):
            self.context_validators.append(validator)
        else:
            raise ValueError("Validator must have a 'validate' method")
