"""Analytics Factory - centralized creation of analytics domain objects."""

from typing import Any

from MVP.analytics.domain.models.kpi_result import (
    BottleneckInfo,
    ContextMetrics,
    KPIResult,
    ThroughputKPI,
    UtilizationKPI,
)
from MVP.analytics.domain.value_objects.metric_value import (
    MetricValue,
)
from MVP.workshop_operations.domain.entities.workshop import (
    Workshop,
)


class AnalyticsFactory:
    """Factory for creating analytics domain objects."""

    @staticmethod
    def create_throughput_kpi(
        total_processed: int,
        total_retrofitted: int,
        total_rejected: int,
        duration_hours: float,
    ) -> ThroughputKPI:
        """Create throughput KPI."""
        wagons_per_hour = (
            total_retrofitted / duration_hours if duration_hours > 0 else 0.0
        )
        return ThroughputKPI(
            total_wagons_processed=total_processed,
            total_wagons_retrofitted=total_retrofitted,
            total_wagons_rejected=total_rejected,
            simulation_duration_hours=duration_hours,
            wagons_per_hour=round(wagons_per_hour, 2),
            wagons_per_day=round(wagons_per_hour * 24.0, 2),
        )

    @staticmethod
    def create_utilization_kpi(
        workshop: Workshop, processed_count: int
    ) -> UtilizationKPI:
        """Create utilization KPI for workshop."""
        total_capacity = workshop.retrofit_stations
        avg_utilization = min(
            100.0,
            (processed_count / total_capacity * 10) if total_capacity > 0 else 0.0,
        )

        return UtilizationKPI(
            id=workshop.id,
            total_capacity=total_capacity,
            average_utilization_percent=round(avg_utilization, 1),
            peak_utilization_percent=round(min(100.0, avg_utilization * 1.2), 1),
            idle_time_percent=round(100.0 - avg_utilization, 1),
        )

    @staticmethod
    def create_bottleneck_info(
        location: str,
        bottleneck_type: str,
        severity: str,
        description: str,
        impact_wagons_per_hour: float,
    ) -> BottleneckInfo:
        """Create bottleneck info."""
        return BottleneckInfo(
            location=location,
            type=bottleneck_type,
            severity=severity,
            description=description,
            impact_wagons_per_hour=impact_wagons_per_hour,
        )

    @staticmethod
    def create_kpi_result(
        scenario_id: str,
        throughput: ThroughputKPI,
        analysis_data: dict[str, Any],
    ) -> KPIResult:
        """Create complete KPI result.

        Parameters
        ----------
        scenario_id : str
            The scenario identifier.
        throughput : ThroughputKPI
            Throughput metrics.
        analysis_data : dict[str, Any]
            Dictionary containing 'utilization', 'bottlenecks', 'avg_flow_time',
            'avg_waiting_time', and 'popup_metrics'.
        """
        return KPIResult(
            scenario_id=scenario_id,
            throughput=throughput,
            utilization=analysis_data["utilization"],
            bottlenecks=analysis_data["bottlenecks"],
            avg_flow_time_minutes=analysis_data["avg_flow_time"],
            avg_waiting_time_minutes=analysis_data["avg_waiting_time"],
            context_metrics=analysis_data.get("context_metrics", ContextMetrics()),
        )

    @staticmethod
    def create_metric_value(value: Any, unit: str = "") -> MetricValue:
        """Create metric value object."""
        return MetricValue(value=value, unit=unit)
