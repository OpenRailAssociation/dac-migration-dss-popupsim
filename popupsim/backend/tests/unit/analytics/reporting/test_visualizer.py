"""Tests for Visualizer chart generation."""

from pathlib import Path

from analytics.models.kpi_result import BottleneckInfo
from analytics.models.kpi_result import KPIResult
from analytics.models.kpi_result import ThroughputKPI
from analytics.models.kpi_result import UtilizationKPI
from analytics.reporting.visualizer import Visualizer
import pytest


@pytest.fixture
def sample_kpi_result() -> KPIResult:
    """Create sample KPI result for testing."""
    return KPIResult(
        scenario_id='test_scenario',
        throughput=ThroughputKPI(
            total_wagons_processed=100,
            total_wagons_retrofitted=85,
            total_wagons_rejected=15,
            simulation_duration_hours=24.0,
            wagons_per_hour=4.17,
            wagons_per_day=100.0,
        ),
        utilization=[
            UtilizationKPI(
                workshop_id='WS1',
                total_capacity=10,
                average_utilization_percent=75.5,
                peak_utilization_percent=95.0,
                idle_time_percent=24.5,
            ),
            UtilizationKPI(
                workshop_id='WS2',
                total_capacity=8,
                average_utilization_percent=60.0,
                peak_utilization_percent=80.0,
                idle_time_percent=40.0,
            ),
        ],
        bottlenecks=[
            BottleneckInfo(
                location='WS1',
                type='capacity',
                severity='high',
                description='Workshop at 95% capacity',
                impact_wagons_per_hour=2.5,
            )
        ],
        avg_flow_time_minutes=120.5,
        avg_waiting_time_minutes=45.3,
    )


@pytest.fixture
def empty_kpi_result() -> KPIResult:
    """Create empty KPI result for edge case testing."""
    return KPIResult(
        scenario_id='empty_scenario',
        throughput=ThroughputKPI(
            total_wagons_processed=0,
            total_wagons_retrofitted=0,
            total_wagons_rejected=0,
            simulation_duration_hours=0.0,
            wagons_per_hour=0.0,
            wagons_per_day=0.0,
        ),
        utilization=[],
        bottlenecks=[],
        avg_flow_time_minutes=0.0,
        avg_waiting_time_minutes=0.0,
    )


def test_visualizer_initialization() -> None:
    """Test Visualizer can be instantiated."""
    visualizer = Visualizer()
    assert visualizer is not None


def test_generate_throughput_chart(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test throughput chart generation."""
    visualizer = Visualizer()
    output_path = tmp_path / 'throughput.png'

    visualizer.generate_throughput_chart(sample_kpi_result, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_utilization_chart(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test utilization chart generation."""
    visualizer = Visualizer()
    output_path = tmp_path / 'utilization.png'

    visualizer.generate_utilization_chart(sample_kpi_result, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_utilization_chart_empty(empty_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test utilization chart with no data."""
    visualizer = Visualizer()
    output_path = tmp_path / 'utilization_empty.png'

    visualizer.generate_utilization_chart(empty_kpi_result, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_timing_chart(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test timing chart generation."""
    visualizer = Visualizer()
    output_path = tmp_path / 'timing.png'

    visualizer.generate_timing_chart(sample_kpi_result, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_all_charts(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test generating all charts at once."""
    visualizer = Visualizer()

    chart_paths = visualizer.generate_all_charts(sample_kpi_result, tmp_path)

    assert len(chart_paths) == 3
    assert all(path.exists() for path in chart_paths)
    assert all(path.stat().st_size > 0 for path in chart_paths)


def test_generate_all_charts_creates_directory(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test that generate_all_charts creates output directory if it doesn't exist."""
    visualizer = Visualizer()
    output_dir = tmp_path / 'charts' / 'nested'

    assert not output_dir.exists()

    chart_paths = visualizer.generate_all_charts(sample_kpi_result, output_dir)

    assert output_dir.exists()
    assert len(chart_paths) == 3


def test_chart_filenames(sample_kpi_result: KPIResult, tmp_path: Path) -> None:
    """Test that generated charts have correct filenames."""
    visualizer = Visualizer()

    chart_paths = visualizer.generate_all_charts(sample_kpi_result, tmp_path)

    filenames = {path.name for path in chart_paths}
    assert filenames == {'throughput.png', 'utilization.png', 'timing.png'}
