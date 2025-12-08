"""Domain service for validating shunting plans."""

from MVP.shunting_operations.domain.entities.shunting_operation import (
    ShuntingOperation,
)
from shared.validation.base import (
    ValidationCategory,
    ValidationResult,
)


class ShuntingPlanValidationError(Exception):
    """Domain-specific validation error."""


class ShuntingPlanValidator:
    """Domain service for shunting plan validation."""

    @staticmethod
    def validate_step_sequence(sequence: int) -> None:
        """Validate step sequence number."""
        if sequence < 0:
            msg = f"Step sequence must be non-negative, got {sequence}"
            raise ShuntingPlanValidationError(msg)

    @staticmethod
    def validate_plan_steps(steps: list[tuple[int, ShuntingOperation]]) -> None:
        """Validate plan step ordering."""
        if not steps:
            msg = "Plan must have at least one step"
            raise ShuntingPlanValidationError(msg)

        sequences = [seq for seq, _ in steps]
        if sequences != sorted(sequences):
            msg = f"Steps must be in sequence order, got {sequences}"
            raise ShuntingPlanValidationError(msg)

    @staticmethod
    def validate_locomotive_consistency(
        locomotive_id: str, steps: list[tuple[int, ShuntingOperation]]
    ) -> None:
        """Validate all operations use same locomotive."""
        for seq, operation in steps:
            if operation.locomotive_id != locomotive_id:
                msg = f"Step {seq}: operation locomotive {operation.locomotive_id} != plan locomotive {locomotive_id}"
                raise ShuntingPlanValidationError(msg)

    @staticmethod
    def validate_to_result(
        locomotive_id: str, steps: list[tuple[int, ShuntingOperation]]
    ) -> ValidationResult:
        """Validate and return ValidationResult instead of throwing."""
        result = ValidationResult(is_valid=True)

        try:
            ShuntingPlanValidator.validate_plan_steps(steps)
            ShuntingPlanValidator.validate_locomotive_consistency(locomotive_id, steps)
        except ShuntingPlanValidationError as e:
            result.add_error(str(e), category=ValidationCategory.SEMANTIC)

        return result
