"""Analytics Factory - centralized creation of analytics domain objects."""

from typing import Any

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.workshop import Workshop

from configuration.domain.models.scenario import Scenario

from ..aggregates.analytics_session import AnalyticsSession
from ..events.base_event import DomainEvent
from ..events.simulation_events import WagonDeliveredEvent
from ..events.simulation_events import WagonRejectedEvent
from ..events.simulation_events import WagonRetrofittedEvent
from ..models.kpi_result import BottleneckInfo
from ..models.kpi_result import KPIResult
from ..models.kpi_result import ThroughputKPI
from ..models.kpi_result import UtilizationKPI
from ..value_objects.event_id import EventId
from ..value_objects.metric_value import MetricValue
from ..value_objects.timestamp import Timestamp


class AnalyticsFactory:
    """Factory for creating analytics domain objects."""

    @staticmethod
    def create_analytics_session(scenario_id: str) -> AnalyticsSession:
        """Create analytics session for scenario."""
        return AnalyticsSession(scenario_id=scenario_id)

    @staticmethod
    def create_simulation_started_event(_scenario: Scenario) -> DomainEvent:
        """Create simulation started event."""
        return DomainEvent(
            event_id=EventId.generate(),
            timestamp=Timestamp.now(),
        )

    @staticmethod
    def create_wagon_delivered_event(wagon: Wagon) -> WagonDeliveredEvent:
        """Create wagon delivered event."""
        return WagonDeliveredEvent(
            event_id=EventId.generate(),
            timestamp=Timestamp.now(),
            wagon_id=wagon.id,
        )

    @staticmethod
    def create_wagon_retrofitted_event(wagon: Wagon, workshop_id: str) -> WagonRetrofittedEvent:
        """Create wagon retrofitted event."""
        return WagonRetrofittedEvent(
            event_id=EventId.generate(),
            timestamp=Timestamp.now(),
            wagon_id=wagon.id,
            workshop_id=workshop_id,
            processing_duration=0.0,
        )

    @staticmethod
    def create_wagon_rejected_event(wagon: Wagon, reason: str) -> WagonRejectedEvent:
        """Create wagon rejected event."""
        return WagonRejectedEvent(
            event_id=EventId.generate(),
            timestamp=Timestamp.now(),
            wagon_id=wagon.id,
            reason=reason,
        )

    @staticmethod
    def create_simulation_completed_event(
        _scenario_id: str, _total_processed: int, _total_rejected: int
    ) -> DomainEvent:
        """Create simulation completed event."""
        return DomainEvent(
            event_id=EventId.generate(),
            timestamp=Timestamp.now(),
        )

    @staticmethod
    def create_throughput_kpi(
        total_processed: int,
        total_retrofitted: int,
        total_rejected: int,
        duration_hours: float,
    ) -> ThroughputKPI:
        """Create throughput KPI."""
        wagons_per_hour = total_retrofitted / duration_hours if duration_hours > 0 else 0.0
        return ThroughputKPI(
            total_wagons_processed=total_processed,
            total_wagons_retrofitted=total_retrofitted,
            total_wagons_rejected=total_rejected,
            simulation_duration_hours=duration_hours,
            wagons_per_hour=round(wagons_per_hour, 2),
            wagons_per_day=round(wagons_per_hour * 24.0, 2),
        )

    @staticmethod
    def create_utilization_kpi(workshop: Workshop, processed_count: int) -> UtilizationKPI:
        """Create utilization KPI for workshop."""
        total_capacity = workshop.retrofit_stations
        avg_utilization = min(100.0, (processed_count / total_capacity * 10) if total_capacity > 0 else 0.0)

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
            Dictionary containing 'utilization', 'bottlenecks', 'avg_flow_time', and 'avg_waiting_time'.
        """
        return KPIResult(
            scenario_id=scenario_id,
            throughput=throughput,
            utilization=analysis_data['utilization'],
            bottlenecks=analysis_data['bottlenecks'],
            avg_flow_time_minutes=analysis_data['avg_flow_time'],
            avg_waiting_time_minutes=analysis_data['avg_waiting_time'],
        )

    @staticmethod
    def create_metric_value(value: Any, unit: str = '') -> MetricValue:
        """Create metric value object."""
        return MetricValue(value=value, unit=unit)
