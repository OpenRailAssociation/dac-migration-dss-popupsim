"""Validation coordinator for cross-context validation."""

from shared.validation.base import ValidationResult
from workshop_operations.domain.services.scenario_domain_validator import WorkshopOperationsValidator

from configuration.domain.models.scenario import Scenario
from configuration.domain.services.configuration_validator import ConfigurationValidator


class ValidationCoordinator:
    """Coordinates validation across all contexts."""

    def __init__(self) -> None:
        """Initialize with context validators."""
        self.validators = [
            ConfigurationValidator(),
            WorkshopOperationsValidator(),
        ]

    def validate_all(self, scenario: Scenario) -> ValidationResult:
        """Validate scenario across all contexts, collecting all issues."""
        result = ValidationResult(is_valid=True)

        for validator in self.validators:
            context_result = validator.validate(scenario)
            result.merge(context_result)

        return result

    def add_validator(self, validator: object) -> None:
        """Add a new context validator."""
        if hasattr(validator, 'validate'):
            self.validators.append(validator)
        else:
            raise ValueError("Validator must have a 'validate' method")
