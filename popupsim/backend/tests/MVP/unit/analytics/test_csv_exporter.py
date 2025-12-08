"""Tests for CSV exporter."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from popupsim.backend.src.MVP.analytics.domain.models.kpi_result import (
    BottleneckInfo,
    KPIResult,
    ThroughputKPI,
    UtilizationKPI,
)
from popupsim.backend.src.MVP.analytics.infrastructure.exporters.csv_exporter import (
    CSVExporter,
)


@pytest.fixture
def sample_kpi_result() -> KPIResult:
    """Create sample KPI result."""
    return KPIResult(
        scenario_id="TEST001",
        throughput=ThroughputKPI(
            total_wagons_processed=100,
            total_wagons_retrofitted=95,
            total_wagons_rejected=5,
            simulation_duration_hours=24.0,
            wagons_per_hour=3.96,
            wagons_per_day=95.0,
        ),
        utilization=[
            UtilizationKPI("WS001", 10, 75.0, 90.0, 25.0),
            UtilizationKPI("WS002", 8, 65.0, 85.0, 35.0),
        ],
        bottlenecks=[
            BottleneckInfo("Track 1", "track", "high", "High rejection rate", 2.5),
        ],
    )


def test_export_kpis(sample_kpi_result: KPIResult) -> None:
    """Test exporting KPIs to CSV."""
    exporter = CSVExporter()

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter.export_kpis(sample_kpi_result, output_dir)

        assert (output_dir / "throughput_kpis.csv").exists()
        assert (output_dir / "utilization_kpis.csv").exists()
        assert (output_dir / "bottlenecks.csv").exists()


def test_throughput_csv_content(sample_kpi_result: KPIResult) -> None:
    """Test throughput CSV content."""
    exporter = CSVExporter()

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter.export_kpis(sample_kpi_result, output_dir)

        df = pd.read_csv(output_dir / "throughput_kpis.csv")
        assert len(df) == 6
        assert "metric" in df.columns
        assert "value" in df.columns


def test_utilization_csv_content(sample_kpi_result: KPIResult) -> None:
    """Test utilization CSV content."""
    exporter = CSVExporter()

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter.export_kpis(sample_kpi_result, output_dir)

        df = pd.read_csv(output_dir / "utilization_kpis.csv")
        assert len(df) == 2
        assert "workshop_id" in df.columns
        assert df["workshop_id"].tolist() == ["WS001", "WS002"]


def test_bottlenecks_csv_content(sample_kpi_result: KPIResult) -> None:
    """Test bottlenecks CSV content."""
    exporter = CSVExporter()

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter.export_kpis(sample_kpi_result, output_dir)

        df = pd.read_csv(output_dir / "bottlenecks.csv")
        assert len(df) == 1
        assert df["location"].iloc[0] == "Track 1"
        assert df["severity"].iloc[0] == "high"


def test_export_time_series() -> None:
    """Test exporting time-series metrics."""
    exporter = CSVExporter()
    metrics = {
        "wagon": [
            {"name": "wagons_delivered", "value": 10, "unit": "wagons"},
            {"name": "wagons_retrofitted", "value": 8, "unit": "wagons"},
        ],
        "locomotive": [
            {"name": "L001_moving_utilization", "value": 75.0, "unit": "%"},
        ],
    }

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        exporter.export_time_series(metrics, output_dir)

        assert (output_dir / "wagon_metrics.csv").exists()
        assert (output_dir / "locomotive_metrics.csv").exists()


def test_export_creates_directory() -> None:
    """Test that export creates output directory."""
    exporter = CSVExporter()

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "nested" / "output"
        exporter.export_time_series({}, output_dir)

        assert output_dir.exists()
