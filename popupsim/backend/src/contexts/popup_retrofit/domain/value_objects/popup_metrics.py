"""PopUp-specific metrics value objects."""

from pydantic import BaseModel, Field

from shared.infrastructure.time_config import SIMULATION_TIME_UNIT_SECONDS


class PopUpMetrics(BaseModel):
    """PopUp workshop performance metrics."""

    total_processing_time: float = Field(
        default=0.0, description="Total time spent processing wagons (minutes)"
    )
    total_wagons_processed: int = Field(
        default=0, description="Total number of wagons processed"
    )
    successful_retrofits: int = Field(
        default=0, description="Number of successful retrofits"
    )

    def record_wagon_processed(self, duration: float, success: bool = True) -> None:
        """Record a processed wagon."""
        self.total_wagons_processed += 1
        self.total_processing_time += duration
        if success:
            self.successful_retrofits += 1

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_wagons_processed == 0:
            return 0.0
        return (self.successful_retrofits / self.total_wagons_processed) * 100.0

    @property
    def average_processing_time(self) -> float:
        """Average time per wagon in minutes."""
        if self.total_wagons_processed == 0:
            return 0.0
        return self.total_processing_time / self.total_wagons_processed

    @property
    def bay_utilization_percentage(self) -> float:
        """Bay utilization as percentage (simplified)."""
        return min(self.wagons_per_hour * 10.0, 100.0)

    @property
    def wagons_per_hour(self) -> float:
        """Throughput in wagons per hour."""
        if self.total_processing_time == 0:
            return 0.0
        return (
            self.total_wagons_processed * SIMULATION_TIME_UNIT_SECONDS
        ) / self.total_processing_time

    def calculate_efficiency_score(self) -> float:
        """Calculate overall PopUp efficiency score (0-100)."""
        utilization_score = min(self.bay_utilization_percentage, 100.0)
        throughput_score = min(self.wagons_per_hour * 10.0, 100.0)
        return (utilization_score + throughput_score) / 2.0

    def get_bottleneck_analysis(self) -> str:
        """Identify primary bottleneck in PopUp operations."""
        if self.bay_utilization_percentage < 60.0:
            return "Low bay utilization - consider reducing bay count or increasing wagon flow"
        if self.wagons_per_hour < 2.0:
            return "Low throughput - optimize retrofit procedures or add more bays"
        return "Operations performing within normal parameters"
