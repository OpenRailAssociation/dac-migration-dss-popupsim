"""4-Layer validation pipeline with error stacking."""

from shared.validation.base import ValidationCategory
from shared.validation.base import ValidationResult
from shared.validation.validators.feasibility_validator import FeasibilityValidator
from shared.validation.validators.integrity_validator import IntegrityValidator
from shared.validation.validators.semantic_validator import SemanticValidator
from shared.validation.validators.syntax_validator import SyntaxValidator

from configuration.domain.models.scenario import Scenario


class ValidationPipeline:
    """4-layer validation pipeline that stacks all errors and warnings."""

    def __init__(self) -> None:
        """Initialize with all validation layers."""
        self.syntax_validator = SyntaxValidator()
        self.semantic_validator = SemanticValidator()
        self.integrity_validator = IntegrityValidator()
        self.feasibility_validator = FeasibilityValidator()

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Run all validation layers and stack errors/warnings."""
        result = ValidationResult(is_valid=True)

        # Layer 1: SYNTAX - Basic field validation
        syntax_result = self.syntax_validator.validate(scenario)
        result.merge(syntax_result)

        # Layer 2: SEMANTIC - Business rules within entities
        semantic_result = self.semantic_validator.validate(scenario)
        result.merge(semantic_result)

        # Layer 3: INTEGRITY - Cross-reference validation
        integrity_result = self.integrity_validator.validate(scenario)
        result.merge(integrity_result)

        # Layer 4: FEASIBILITY - Operational constraints
        feasibility_result = self.feasibility_validator.validate(scenario)
        result.merge(feasibility_result)

        return result

    def validate_layer(self, scenario: Scenario, category: ValidationCategory) -> ValidationResult:
        """Validate specific layer only (for testing/debugging)."""
        if category == ValidationCategory.SYNTAX:
            return self.syntax_validator.validate(scenario)
        if category == ValidationCategory.SEMANTIC:
            return self.semantic_validator.validate(scenario)
        if category == ValidationCategory.INTEGRITY:
            return self.integrity_validator.validate(scenario)
        if category == ValidationCategory.FEASIBILITY:
            return self.feasibility_validator.validate(scenario)
        raise ValueError(f'Unknown validation category: {category}')
