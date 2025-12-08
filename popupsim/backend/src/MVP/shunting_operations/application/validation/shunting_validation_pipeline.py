"""Integrated validation pipeline for shunting operations."""

from typing import Any

from MVP.shunting_operations.domain.entities.shunting_operation import (
    ShuntingOperation,
)
from MVP.shunting_operations.domain.services.shunting_plan_validator import (
    ShuntingPlanValidationError,
    ShuntingPlanValidator,
)
from shared.validation.base import (
    ValidationCategory,
    ValidationResult,
)
from shared.validation.pipeline import ValidationPipeline


class ShuntingValidationPipeline:
    """Integrated validation combining shared pipeline with domain validation."""

    def __init__(self) -> None:
        self.shared_pipeline = ValidationPipeline()

    def validate_plan_data(self, plan_data: dict[str, Any]) -> ValidationResult:
        """Validate raw plan data through 4-layer pipeline."""
        result = ValidationResult(is_valid=True)

        # Layer 1: SYNTAX - Basic format validation
        self._validate_syntax(plan_data, result)

        # Layer 2: SEMANTIC - Business rules
        self._validate_semantic(plan_data, result)

        # Layer 3: INTEGRITY - Cross-references
        self._validate_integrity(plan_data, result)

        # Layer 4: FEASIBILITY - Operational constraints
        self._validate_feasibility(plan_data, result)

        return result

    def validate_domain_objects(
        self, locomotive_id: str, operations: list[tuple[int, ShuntingOperation]]
    ) -> ValidationResult:
        """Validate domain objects using domain services."""
        result = ValidationResult(is_valid=True)

        try:
            # Use domain service for validation
            ShuntingPlanValidator.validate_plan_steps(operations)
            ShuntingPlanValidator.validate_locomotive_consistency(
                locomotive_id, operations
            )
        except ShuntingPlanValidationError as e:
            result.add_error(
                str(e),
                category=ValidationCategory.SEMANTIC,
                suggestion="Check plan structure and locomotive assignments",
            )

        return result

    def _validate_syntax(self, data: dict[str, Any], result: ValidationResult) -> None:
        """Layer 1: Format and type validation."""
        if not isinstance(data.get("plan_id"), str):
            result.add_error(
                "plan_id must be string",
                field_name="plan_id",
                category=ValidationCategory.SYNTAX,
            )

        if not isinstance(data.get("locomotive_id"), str):
            result.add_error(
                "locomotive_id must be string",
                field_name="locomotive_id",
                category=ValidationCategory.SYNTAX,
            )

        if not isinstance(data.get("steps"), list):
            result.add_error(
                "steps must be list",
                field_name="steps",
                category=ValidationCategory.SYNTAX,
            )

    def _validate_semantic(
        self, data: dict[str, Any], result: ValidationResult
    ) -> None:
        """Layer 2: Business rules validation."""
        steps = data.get("steps", [])
        if len(steps) == 0:
            result.add_error(
                "Plan must have at least one step", category=ValidationCategory.SEMANTIC
            )

    def _validate_integrity(
        self, data: dict[str, Any], result: ValidationResult
    ) -> None:
        """Layer 3: Cross-reference validation."""
        # Check sequence ordering
        steps = data.get("steps", [])
        sequences = [
            step.get("sequence", -1) for step in steps if isinstance(step, dict)
        ]
        if sequences != sorted(sequences):
            result.add_error(
                "Steps must be in sequence order", category=ValidationCategory.INTEGRITY
            )

    def _validate_feasibility(
        self, data: dict[str, Any], result: ValidationResult
    ) -> None:
        """Layer 4: Operational constraints."""
        steps = data.get("steps", [])
        if len(steps) > 50:
            result.add_warning(
                "Large plans may impact performance",
                category=ValidationCategory.FEASIBILITY,
            )
