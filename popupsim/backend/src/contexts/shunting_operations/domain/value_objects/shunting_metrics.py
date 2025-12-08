"""Shunting operations metrics."""

from pydantic import BaseModel, Field


class ShuntingMetrics(BaseModel):
    """Metrics for shunting operations."""

    total_operations: int = Field(
        default=0, description="Total shunting operations performed"
    )
    successful_operations: int = Field(default=0, description="Successful operations")
    total_operation_time: float = Field(
        default=0.0, description="Total time spent on operations (minutes)"
    )
    locomotives_allocated: int = Field(
        default=0, description="Number of locomotives allocated"
    )

    def record_operation(self, duration: float, success: bool = True) -> None:
        """Record a shunting operation."""
        self.total_operations += 1
        self.total_operation_time += duration
        if success:
            self.successful_operations += 1

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100.0

    @property
    def average_operation_time(self) -> float:
        """Average operation time in minutes."""
        if self.total_operations == 0:
            return 0.0
        return self.total_operation_time / self.total_operations
