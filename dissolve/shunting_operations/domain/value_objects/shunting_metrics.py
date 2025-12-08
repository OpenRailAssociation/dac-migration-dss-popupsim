"""Shunting operations metrics value objects."""

from pydantic import BaseModel, Field


class ShuntingMetrics(BaseModel):
    """Shunting operations performance metrics."""

    locomotive_id: str = Field(description="Locomotive identifier")
    total_movements: int = Field(default=0, description="Total shunting movements")
    total_coupling_operations: int = Field(
        default=0, description="Total coupling operations"
    )
    total_active_time: float = Field(
        default=0.0, description="Total active time (minutes)"
    )
    total_idle_time: float = Field(default=0.0, description="Total idle time (minutes)")

    @property
    def utilization_percentage(self) -> float:
        """Locomotive utilization as percentage."""
        total_time = self.total_active_time + self.total_idle_time
        if total_time == 0:
            return 0.0
        return (self.total_active_time / total_time) * 100.0

    @property
    def movements_per_hour(self) -> float:
        """Movement throughput per hour."""
        if self.total_active_time == 0:
            return 0.0
        return (self.total_movements * 60.0) / self.total_active_time
