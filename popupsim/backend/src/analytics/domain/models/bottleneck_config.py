"""Bottleneck detection configuration models."""

from typing import Dict
from pydantic import BaseModel, Field


class WorkshopThresholds(BaseModel):
    """Workshop-specific bottleneck thresholds."""

    high_utilization_percent: float = Field(default=85.0, ge=0.0, le=100.0)
    critical_utilization_percent: float = Field(default=95.0, ge=0.0, le=100.0)
    min_throughput_wagons_per_hour: float = Field(default=8.0, ge=0.0)


class YardThresholds(BaseModel):
    """Yard operations bottleneck thresholds."""

    max_queue_length: int = Field(default=50, ge=0)
    max_waiting_time_minutes: float = Field(default=120.0, ge=0.0)
    high_rejection_rate_percent: float = Field(default=12.0, ge=0.0, le=100.0)


class ShuntingThresholds(BaseModel):
    """Shunting operations bottleneck thresholds."""

    max_locomotive_utilization_percent: float = Field(default=90.0, ge=0.0, le=100.0)
    max_coupling_time_minutes: float = Field(default=15.0, ge=0.0)
    min_shunting_efficiency_percent: float = Field(default=75.0, ge=0.0, le=100.0)


class BottleneckConfig(BaseModel):
    """Complete bottleneck detection configuration."""

    workshop: WorkshopThresholds = Field(default_factory=WorkshopThresholds)
    yard: YardThresholds = Field(default_factory=YardThresholds)
    shunting: ShuntingThresholds = Field(default_factory=ShuntingThresholds)

    # Global thresholds
    global_rejection_rate_percent: float = Field(default=10.0, ge=0.0, le=100.0)

    @classmethod
    def create_for_scenario(cls, scenario_id: str, overrides: Dict[str, any] = None) -> 'BottleneckConfig':
        """Create configuration with scenario-specific overrides."""
        config = cls()
        if overrides:
            # Apply overrides using Pydantic's model validation
            config = cls.model_validate({**config.model_dump(), **overrides})
        return config
