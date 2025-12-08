"""Tests for KPI result models."""

from popupsim.backend.src.MVP.analytics.domain.models.kpi_result import (
    BottleneckInfo,
    KPIResult,
    ThroughputKPI,
    UtilizationKPI,
)


def test_throughput_kpi_creation() -> None:
    """Test ThroughputKPI creation."""
    kpi = ThroughputKPI(
        total_wagons_processed=100,
        total_wagons_retrofitted=95,
        total_wagons_rejected=5,
        simulation_duration_hours=24.0,
        wagons_per_hour=3.96,
        wagons_per_day=95.0,
    )

    assert kpi.total_wagons_processed == 100
    assert kpi.total_wagons_retrofitted == 95
    assert kpi.total_wagons_rejected == 5
    assert kpi.simulation_duration_hours == 24.0
    assert kpi.wagons_per_hour == 3.96
    assert kpi.wagons_per_day == 95.0


def test_utilization_kpi_creation() -> None:
    """Test UtilizationKPI creation."""
    kpi = UtilizationKPI(
        id="WS001",
        total_capacity=10,
        average_utilization_percent=75.5,
        peak_utilization_percent=95.0,
        idle_time_percent=24.5,
    )

    assert kpi.id == "WS001"
    assert kpi.total_capacity == 10
    assert kpi.average_utilization_percent == 75.5
    assert kpi.peak_utilization_percent == 95.0
    assert kpi.idle_time_percent == 24.5


def test_bottleneck_info_creation() -> None:
    """Test BottleneckInfo creation."""
    bottleneck = BottleneckInfo(
        location="Workshop A",
        type="workshop",
        severity="high",
        description="High utilization detected",
        impact_wagons_per_hour=2.5,
    )

    assert bottleneck.location == "Workshop A"
    assert bottleneck.type == "workshop"
    assert bottleneck.severity == "high"
    assert bottleneck.description == "High utilization detected"
    assert bottleneck.impact_wagons_per_hour == 2.5


def test_kpi_result_creation() -> None:
    """Test KPIResult creation with all fields."""
    throughput = ThroughputKPI(
        total_wagons_processed=100,
        total_wagons_retrofitted=95,
        total_wagons_rejected=5,
        simulation_duration_hours=24.0,
        wagons_per_hour=3.96,
        wagons_per_day=95.0,
    )

    utilization = [
        UtilizationKPI(
            id="WS001",
            total_capacity=10,
            average_utilization_percent=75.0,
            peak_utilization_percent=90.0,
            idle_time_percent=25.0,
        )
    ]

    bottlenecks = [
        BottleneckInfo(
            location="Track 1",
            type="track",
            severity="medium",
            description="Moderate congestion",
            impact_wagons_per_hour=1.5,
        )
    ]

    kpi_result = KPIResult(
        scenario_id="TEST001",
        throughput=throughput,
        utilization=utilization,
        bottlenecks=bottlenecks,
        avg_flow_time_minutes=45.5,
        avg_waiting_time_minutes=12.3,
    )

    assert kpi_result.scenario_id == "TEST001"
    assert kpi_result.throughput == throughput
    assert len(kpi_result.utilization) == 1
    assert len(kpi_result.bottlenecks) == 1
    assert kpi_result.avg_flow_time_minutes == 45.5
    assert kpi_result.avg_waiting_time_minutes == 12.3


def test_kpi_result_with_defaults() -> None:
    """Test KPIResult with default values."""
    throughput = ThroughputKPI(
        total_wagons_processed=50,
        total_wagons_retrofitted=50,
        total_wagons_rejected=0,
        simulation_duration_hours=12.0,
        wagons_per_hour=4.17,
        wagons_per_day=100.0,
    )

    kpi_result = KPIResult(
        scenario_id="TEST002",
        throughput=throughput,
    )

    assert kpi_result.scenario_id == "TEST002"
    assert kpi_result.utilization == []
    assert kpi_result.bottlenecks == []
    assert kpi_result.avg_flow_time_minutes == 0.0
    assert kpi_result.avg_waiting_time_minutes == 0.0


def test_multiple_utilization_kpis() -> None:
    """Test KPIResult with multiple workshop utilizations."""
    throughput = ThroughputKPI(
        total_wagons_processed=200,
        total_wagons_retrofitted=190,
        total_wagons_rejected=10,
        simulation_duration_hours=48.0,
        wagons_per_hour=3.96,
        wagons_per_day=95.0,
    )

    utilization = [
        UtilizationKPI("WS001", 10, 80.0, 95.0, 20.0),
        UtilizationKPI("WS002", 15, 65.0, 85.0, 35.0),
        UtilizationKPI("WS003", 8, 90.0, 100.0, 10.0),
    ]

    kpi_result = KPIResult(
        scenario_id="TEST003",
        throughput=throughput,
        utilization=utilization,
    )

    assert len(kpi_result.utilization) == 3
    assert kpi_result.utilization[0].id == "WS001"
    assert kpi_result.utilization[1].id == "WS002"
    assert kpi_result.utilization[2].id == "WS003"


def test_multiple_bottlenecks() -> None:
    """Test KPIResult with multiple bottlenecks."""
    throughput = ThroughputKPI(
        total_wagons_processed=150,
        total_wagons_retrofitted=140,
        total_wagons_rejected=10,
        simulation_duration_hours=36.0,
        wagons_per_hour=3.89,
        wagons_per_day=93.3,
    )

    bottlenecks = [
        BottleneckInfo("Track 1", "track", "high", "High rejection rate", 2.0),
        BottleneckInfo("WS001", "workshop", "critical", "Overutilized", 3.5),
        BottleneckInfo("Resource Pool", "resource", "medium", "Limited staff", 1.2),
    ]

    kpi_result = KPIResult(
        scenario_id="TEST004",
        throughput=throughput,
        bottlenecks=bottlenecks,
    )

    assert len(kpi_result.bottlenecks) == 3
    assert kpi_result.bottlenecks[0].severity == "high"
    assert kpi_result.bottlenecks[1].severity == "critical"
    assert kpi_result.bottlenecks[2].severity == "medium"


def test_bottleneck_severity_levels() -> None:
    """Test different bottleneck severity levels."""
    severities = ["low", "medium", "high", "critical"]

    for severity in severities:
        bottleneck = BottleneckInfo(
            location="Test Location",
            type="workshop",
            severity=severity,
            description=f"{severity} severity test",
            impact_wagons_per_hour=1.0,
        )
        assert bottleneck.severity == severity


def test_bottleneck_types() -> None:
    """Test different bottleneck types."""
    types = ["track", "workshop", "resource"]

    for btype in types:
        bottleneck = BottleneckInfo(
            location="Test Location",
            type=btype,
            severity="medium",
            description=f"{btype} type test",
            impact_wagons_per_hour=1.0,
        )
        assert bottleneck.type == btype
