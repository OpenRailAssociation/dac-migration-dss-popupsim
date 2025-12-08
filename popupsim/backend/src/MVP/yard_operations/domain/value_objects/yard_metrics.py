"""Yard operations metrics value objects."""

from pydantic import BaseModel, Field

from .rejection_reason import RejectionStats


class YardMetrics(BaseModel):
    """Yard operations performance metrics focused on hump operations."""

    yard_id: str = Field(description="Yard identifier")
    total_wagons_processed: int = Field(
        default=0, description="Total wagons processed through hump"
    )
    total_wagons_classified: int = Field(
        default=0, description="Total wagons successfully classified"
    )
    total_wagons_rejected: int = Field(
        default=0, description="Total wagons rejected at hump"
    )
    total_hump_time: float = Field(
        default=0.0, description="Total hump processing time (minutes)"
    )
    rejection_stats: RejectionStats = Field(
        default_factory=RejectionStats, description="Detailed rejection statistics"
    )
    peak_rejection_rate: float = Field(
        default=0.0, description="Peak rejection rate during simulation"
    )

    @property
    def hump_rejection_rate(self) -> float:
        """Hump rejection rate as percentage - key bottleneck indicator."""
        if self.total_wagons_processed == 0:
            return 0.0
        return (self.total_wagons_rejected / self.total_wagons_processed) * 100.0

    @property
    def hump_success_rate(self) -> float:
        """Hump classification success rate as percentage."""
        return 100.0 - self.hump_rejection_rate

    @property
    def hump_throughput_per_hour(self) -> float:
        """Hump throughput in wagons per hour."""
        if self.total_hump_time == 0:
            return 0.0
        return (self.total_wagons_processed * 60.0) / self.total_hump_time

    def get_bottleneck_analysis(self) -> str:
        """Analyze hump performance for bottlenecks."""
        if self.hump_rejection_rate > 20.0:
            top_reason = self.rejection_stats.get_top_rejection_reason()
            return f"Critical hump bottleneck: {self.hump_rejection_rate:.1f}% rejection rate. Top reason: {top_reason}"
        if self.hump_rejection_rate > 10.0:
            top_reason = self.rejection_stats.get_top_rejection_reason()
            return f"High hump rejection rate: {self.hump_rejection_rate:.1f}%. Main cause: {top_reason}"
        if self.hump_throughput_per_hour < 30.0:
            return (
                f"Low hump throughput: {self.hump_throughput_per_hour:.1f} wagons/hour"
            )
        return "Hump operations performing within normal parameters"

    def get_rejection_summary(self) -> dict[str, float]:
        """Get detailed breakdown of rejection reasons."""
        return self.rejection_stats.get_rejection_breakdown()
