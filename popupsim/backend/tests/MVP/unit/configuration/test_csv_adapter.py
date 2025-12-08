"""Tests for CSV data source adapter."""

from pathlib import Path

import pytest

from popupsim.backend.src.MVP.configuration.application.scenario_loader import (
    ScenarioLoader,
)
from popupsim.backend.src.MVP.configuration.infrastructure.adapters.csv_data_source_adapter import (
    CsvDataSourceAdapter,
)
from popupsim.backend.src.MVP.configuration.infrastructure.adapters.data_source_factory import (
    DataSourceFactory,
)


@pytest.fixture
def csv_scenario_path() -> Path:
    """Path to CSV scenario example."""
    return (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "Data"
        / "examples"
        / "csv_scenario"
    )


@pytest.mark.xfail(reason="CSV adapter not yet implemented")
@pytest.mark.unit
def test_csv_adapter_validation(csv_scenario_path: Path) -> None:
    """Test CSV adapter source validation."""
    adapter = CsvDataSourceAdapter()

    # Valid CSV directory
    assert adapter.validate_source(csv_scenario_path) is True

    # Invalid path
    assert adapter.validate_source(Path("/nonexistent")) is False


@pytest.mark.xfail(reason="CSV adapter not yet implemented")
@pytest.mark.unit
def test_csv_adapter_metadata(csv_scenario_path: Path) -> None:
    """Test CSV adapter metadata retrieval."""
    adapter = CsvDataSourceAdapter()
    metadata = adapter.get_source_metadata(csv_scenario_path)

    assert metadata["source_type"] == "csv"
    assert metadata["directory"] == str(csv_scenario_path)
    assert len(metadata["files"]) > 0

    # Check that scenario.csv is present
    file_names = metadata["files"]
    assert "scenario.csv" in file_names


@pytest.mark.xfail(reason="CSV adapter implementation needs pandas integration testing")
@pytest.mark.unit
def test_csv_adapter_load_scenario(csv_scenario_path: Path) -> None:
    """Test CSV adapter scenario loading."""
    adapter = CsvDataSourceAdapter()
    scenario_dto = adapter.load_scenario(csv_scenario_path)

    assert scenario_dto.id == "csv_example"
    assert scenario_dto.start_date == "2025-01-15"
    assert scenario_dto.end_date == "2025-01-16"
    assert scenario_dto.train_schedule_file == "trains.csv"
    assert scenario_dto.workshop_tracks_file == "workshops.csv"


@pytest.mark.xfail(reason="CSV adapter not yet implemented")
@pytest.mark.unit
def test_data_source_factory_csv_detection(csv_scenario_path: Path) -> None:
    """Test factory correctly detects CSV source type."""
    adapter = DataSourceFactory.create_adapter(csv_scenario_path)
    assert isinstance(adapter, CsvDataSourceAdapter)


@pytest.mark.xfail(reason="CSV adapter not yet implemented")
@pytest.mark.unit
def test_scenario_loader_with_csv(csv_scenario_path: Path) -> None:
    """Test scenario loader with CSV adapter."""
    loader = ScenarioLoader()

    # Test source info
    info = loader.get_source_info(csv_scenario_path)
    assert info["source_type"] == "csv"
    assert info["valid"] is True


@pytest.mark.unit
def test_supported_source_types() -> None:
    """Test supported source types listing."""
    types = ScenarioLoader.get_supported_sources()
    assert "csv" in types
    assert "json" in types
