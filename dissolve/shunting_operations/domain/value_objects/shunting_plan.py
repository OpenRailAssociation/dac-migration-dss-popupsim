"""Shunting plan value objects."""

from dataclasses import dataclass

from ..entities.shunting_operation import ShuntingOperation
from ..services.shunting_plan_validator import ShuntingPlanValidator


@dataclass(frozen=True)
class ShuntingStep:
    """Single step in shunting plan."""

    sequence: int
    operation: ShuntingOperation

    @classmethod
    def create(cls, sequence: int, operation: ShuntingOperation) -> "ShuntingStep":
        """Create validated step."""
        ShuntingPlanValidator.validate_step_sequence(sequence)
        return cls(sequence=sequence, operation=operation)


@dataclass(frozen=True)
class ShuntingPlan:
    """Immutable plan for shunting operations."""

    plan_id: str
    locomotive_id: str
    steps: list[ShuntingStep]

    @classmethod
    def create(
        cls, plan_id: str, locomotive_id: str, steps: list[ShuntingStep]
    ) -> "ShuntingPlan":
        """Create validated plan."""
        step_tuples = [(step.sequence, step.operation) for step in steps]
        ShuntingPlanValidator.validate_plan_steps(step_tuples)
        ShuntingPlanValidator.validate_locomotive_consistency(
            locomotive_id, step_tuples
        )
        return cls(plan_id=plan_id, locomotive_id=locomotive_id, steps=steps)

    @property
    def total_duration(self) -> float:
        """Calculate total estimated duration."""
        return sum(step.operation.estimated_duration for step in self.steps)

    @property
    def step_count(self) -> int:
        """Get number of steps."""
        return len(self.steps)
