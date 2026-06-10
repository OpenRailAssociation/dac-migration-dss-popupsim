"""Task Priority Input DTO for configuration validation."""

from pydantic import BaseModel
from pydantic import Field


class PriorityRuleInputDTO(BaseModel):
    """DTO for a single priority rule."""

    condition: str
    threshold: float = 0.0
    priority: int


class HoldConditionInputDTO(BaseModel):
    """DTO for a hold condition that gates task submission."""

    condition: str
    threshold: float = 0.0


class TaskPriorityInputDTO(BaseModel):
    """DTO for task priority configuration."""

    base_priority: int = 3
    rules: list[PriorityRuleInputDTO] = Field(default_factory=list)
    hold_until: HoldConditionInputDTO | None = None
