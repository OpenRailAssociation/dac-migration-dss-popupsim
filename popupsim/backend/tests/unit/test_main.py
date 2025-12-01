"""Unit tests for the main entry point module."""

from collections.abc import Generator
from datetime import UTC
from datetime import datetime
from pathlib import Path
import tempfile

from main import APP_NAME
from main import app
from main import validate_output_path
from main import validate_scenario_path
import pytest
from pytest_mock import MockerFixture
import typer
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Provide a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_scenario_file() -> Generator[Path]:
    """Create a temporary scenario file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "data"}')
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_output_dir() -> Generator[Path]:
    """Create a temporary output directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.mark.unit
def test_app_name() -> None:
    """Test that APP_NAME constant is correctly set."""
    assert APP_NAME == 'popupsim'


@pytest.mark.unit
def test_main_with_no_parameters(runner: CliRunner) -> None:
    """Test main function shows help when no parameters are provided."""
    result = runner.invoke(app, [])

    assert result.exit_code == 1
    assert 'No required parameters provided. Showing help:' in result.stdout


@pytest.mark.unit
def test_main_with_missing_scenario_path(runner: CliRunner, temp_output_dir: Path) -> None:
    """Test main function fails when scenario path is missing."""
    result = runner.invoke(app, ['--outputPath', str(temp_output_dir)])

    # This should fail because scenario path is missing, not show help
    assert result.exit_code != 0
    assert 'Error: Scenario path is required but not provided' in result.stdout


@pytest.mark.unit
def test_main_with_missing_output_path(runner: CliRunner, temp_scenario_file: Path) -> None:
    """Test main function fails when output path is missing."""
    result = runner.invoke(app, ['--scenarioPath', str(temp_scenario_file)])

    # This should fail because output path is missing, not show help
    assert result.exit_code == 1
    assert 'Error: Output path is required but not provided' in result.stdout


@pytest.mark.unit
def test_main_with_invalid_debug_level(runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path) -> None:
    """Test main function fails with invalid debug level."""
    result = runner.invoke(
        app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir), '--debug', 'INVALID']
    )

    assert result.exit_code == 1
    assert 'Error: Invalid debug level: INVALID' in result.stdout


@pytest.mark.unit
def test_main_with_valid_parameters(
    mocker: MockerFixture, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function succeeds with valid parameters."""
    mock_scenario_builder = mocker.patch('main.ScenarioBuilder')
    mock_builder_instance = mocker.MagicMock()
    mock_scenario = mocker.MagicMock()
    mock_scenario.id = 'test_scenario'
    mock_scenario.start_date = datetime(2024, 1, 1, tzinfo=UTC)
    mock_scenario.end_date = datetime(2024, 12, 31, tzinfo=UTC)
    mock_scenario.trains = []
    mock_scenario.workshops = []
    mock_scenario.routes = []
    mock_builder_instance.build.return_value = mock_scenario
    mock_scenario_builder.return_value = mock_builder_instance

    # Mock the simulation components
    mock_sim_adapter = mocker.patch('main.SimPyAdapter')
    mock_orchestrator = mocker.patch('main.WorkshopOrchestrator')
    mock_orchestrator_instance = mocker.MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.get_metrics.return_value = {}
    mock_orchestrator_instance.wagons_queue = []
    mock_orchestrator_instance.rejected_wagons_queue = []
    mock_orchestrator_instance.workshops_queue = []
    mock_orchestrator_instance.popup_retrofit = None
    mock_orchestrator_instance.yard_operations = None

    # Mock the async analytics service
    mock_analytics_service = mocker.patch('main.AsyncAnalyticsService')
    mock_analytics_instance = mocker.MagicMock()
    mock_analytics_service.return_value = mock_analytics_instance

    # Mock the KPI result
    mock_kpi_result = mocker.MagicMock()
    mock_kpi_result.throughput.total_wagons_processed = 0
    mock_kpi_result.throughput.total_wagons_retrofitted = 0
    mock_kpi_result.throughput.total_wagons_rejected = 0
    mock_kpi_result.throughput.simulation_duration_hours = 0.0
    mock_kpi_result.throughput.wagons_per_hour = 0.0
    mock_kpi_result.throughput.wagons_per_day = 0.0
    mock_kpi_result.utilization = []
    mock_kpi_result.bottlenecks = []
    mock_kpi_result.avg_flow_time_minutes = 0.0
    mock_kpi_result.avg_waiting_time_minutes = 0.0

    # Create an async mock that returns the KPI result
    async def mock_calculate_kpis_async(*args, **kwargs):
        return mock_kpi_result

    mock_analytics_instance.calculate_kpis_async = mock_calculate_kpis_async

    # Mock the exporters
    mocker.patch('main.CSVExporter')
    mocker.patch('main.Visualizer')

    result = runner.invoke(app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir)])

    assert result.exit_code == 0
    assert f'Using scenario file at: {temp_scenario_file}' in result.stdout
    assert f'Output will be saved to: {temp_output_dir}' in result.stdout
    assert 'Debug level set to: INFO' in result.stdout
    assert 'Starting simulation...' in result.stdout


@pytest.mark.unit
def test_main_with_verbose_flag(
    mocker: MockerFixture, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function with verbose flag enabled."""
    mock_scenario_builder = mocker.patch('main.ScenarioBuilder')
    mock_builder_instance = mocker.MagicMock()
    mock_scenario = mocker.MagicMock()
    mock_scenario.id = 'test_scenario'
    mock_scenario.start_date = datetime(2024, 1, 1, tzinfo=UTC)
    mock_scenario.end_date = datetime(2024, 12, 31, tzinfo=UTC)
    mock_scenario.trains = []
    mock_scenario.workshops = []
    mock_scenario.routes = []
    mock_builder_instance.build.return_value = mock_scenario
    mock_scenario_builder.return_value = mock_builder_instance

    # Mock the simulation components
    mock_sim_adapter = mocker.patch('main.SimPyAdapter')
    mock_orchestrator = mocker.patch('main.WorkshopOrchestrator')
    mock_orchestrator_instance = mocker.MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.get_metrics.return_value = {}
    mock_orchestrator_instance.wagons_queue = []
    mock_orchestrator_instance.rejected_wagons_queue = []
    mock_orchestrator_instance.workshops_queue = []
    mock_orchestrator_instance.popup_retrofit = None
    mock_orchestrator_instance.yard_operations = None

    # Mock the async analytics service
    mock_analytics_service = mocker.patch('main.AsyncAnalyticsService')
    mock_analytics_instance = mocker.MagicMock()
    mock_analytics_service.return_value = mock_analytics_instance

    # Mock the KPI result
    mock_kpi_result = mocker.MagicMock()
    mock_kpi_result.throughput.total_wagons_processed = 0
    mock_kpi_result.throughput.total_wagons_retrofitted = 0
    mock_kpi_result.throughput.total_wagons_rejected = 0
    mock_kpi_result.throughput.simulation_duration_hours = 0.0
    mock_kpi_result.throughput.wagons_per_hour = 0.0
    mock_kpi_result.throughput.wagons_per_day = 0.0
    mock_kpi_result.utilization = []
    mock_kpi_result.bottlenecks = []
    mock_kpi_result.avg_flow_time_minutes = 0.0
    mock_kpi_result.avg_waiting_time_minutes = 0.0

    # Create an async mock that returns the KPI result
    async def mock_calculate_kpis_async(*args, **kwargs):
        return mock_kpi_result

    mock_analytics_instance.calculate_kpis_async = mock_calculate_kpis_async

    # Mock the exporters
    mocker.patch('main.CSVExporter')
    mocker.patch('main.Visualizer')

    result = runner.invoke(
        app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir), '--verbose']
    )

    assert result.exit_code == 0
    assert 'Verbose mode enabled.' in result.stdout


@pytest.mark.unit
def test_main_with_custom_debug_level(
    mocker: MockerFixture, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function with custom debug level."""
    mock_scenario_builder = mocker.patch('main.ScenarioBuilder')
    mock_builder_instance = mocker.MagicMock()
    mock_scenario = mocker.MagicMock()
    mock_scenario.id = 'test_scenario'
    mock_scenario.start_date = datetime(2024, 1, 1, tzinfo=UTC)
    mock_scenario.end_date = datetime(2024, 12, 31, tzinfo=UTC)
    mock_scenario.trains = []
    mock_scenario.workshops = []
    mock_scenario.routes = []
    mock_builder_instance.build.return_value = mock_scenario
    mock_scenario_builder.return_value = mock_builder_instance

    # Mock the simulation components
    mock_sim_adapter = mocker.patch('main.SimPyAdapter')
    mock_orchestrator = mocker.patch('main.WorkshopOrchestrator')
    mock_orchestrator_instance = mocker.MagicMock()
    mock_orchestrator.return_value = mock_orchestrator_instance
    mock_orchestrator_instance.get_metrics.return_value = {}
    mock_orchestrator_instance.wagons_queue = []
    mock_orchestrator_instance.rejected_wagons_queue = []
    mock_orchestrator_instance.workshops_queue = []
    mock_orchestrator_instance.popup_retrofit = None
    mock_orchestrator_instance.yard_operations = None

    # Mock the async analytics service
    mock_analytics_service = mocker.patch('main.AsyncAnalyticsService')
    mock_analytics_instance = mocker.MagicMock()
    mock_analytics_service.return_value = mock_analytics_instance

    # Mock the KPI result
    mock_kpi_result = mocker.MagicMock()
    mock_kpi_result.throughput.total_wagons_processed = 0
    mock_kpi_result.throughput.total_wagons_retrofitted = 0
    mock_kpi_result.throughput.total_wagons_rejected = 0
    mock_kpi_result.throughput.simulation_duration_hours = 0.0
    mock_kpi_result.throughput.wagons_per_hour = 0.0
    mock_kpi_result.throughput.wagons_per_day = 0.0
    mock_kpi_result.utilization = []
    mock_kpi_result.bottlenecks = []
    mock_kpi_result.avg_flow_time_minutes = 0.0
    mock_kpi_result.avg_waiting_time_minutes = 0.0

    # Create an async mock that returns the KPI result
    async def mock_calculate_kpis_async(*args, **kwargs):
        return mock_kpi_result

    mock_analytics_instance.calculate_kpis_async = mock_calculate_kpis_async

    # Mock the exporters
    mocker.patch('main.CSVExporter')
    mocker.patch('main.Visualizer')

    result = runner.invoke(
        app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir), '--debug', 'DEBUG']
    )

    assert result.exit_code == 0
    assert 'Debug level set to: DEBUG' in result.stdout


@pytest.mark.unit
def test_validate_scenario_path_none() -> None:
    """Test validate_scenario_path with None input."""
    with pytest.raises(typer.Exit) as exc_info:
        validate_scenario_path(None)

    assert exc_info.value.exit_code == 1


@pytest.mark.unit
def test_validate_scenario_path_nonexistent() -> None:
    """Test validate_scenario_path with non-existent file."""
    nonexistent_path = Path('/nonexistent/file.json')
    with pytest.raises(typer.Exit):
        validate_scenario_path(nonexistent_path)


@pytest.mark.unit
def test_validate_scenario_path_directory(temp_output_dir: Path) -> None:
    """Test validate_scenario_path with directory instead of file."""
    with pytest.raises(typer.Exit):
        validate_scenario_path(temp_output_dir)


@pytest.mark.unit
def test_validate_scenario_path_valid(temp_scenario_file: Path) -> None:
    """Test validate_scenario_path with valid file."""
    result = validate_scenario_path(temp_scenario_file)
    assert result == temp_scenario_file


@pytest.mark.unit
def test_validate_output_path_none() -> None:
    """Test validate_output_path with None input."""
    with pytest.raises(typer.Exit):
        validate_output_path(None)


@pytest.mark.unit
def test_validate_output_path_nonexistent() -> None:
    """Test validate_output_path with non-existent directory."""
    nonexistent_path = Path('/nonexistent/directory')
    with pytest.raises(typer.Exit):
        validate_output_path(nonexistent_path)


@pytest.mark.unit
def test_validate_output_path_file(temp_scenario_file: Path) -> None:
    """Test validate_output_path with file instead of directory."""
    with pytest.raises(typer.Exit):
        validate_output_path(temp_scenario_file)


@pytest.mark.unit
def test_validate_output_path_valid(temp_output_dir: Path) -> None:
    """Test validate_output_path with valid directory."""
    result = validate_output_path(temp_output_dir)
    assert result == temp_output_dir


@pytest.mark.unit
def test_validate_output_path_write_permission() -> None:
    """Test validate_output_path write permission check."""
    # Test with a read-only directory (if possible to create)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # This test might be platform-dependent
        result = validate_output_path(temp_path)
        assert result == temp_path


@pytest.mark.unit
def test_app_configuration() -> None:
    """Test that the Typer app is configured correctly."""
    assert app.info.name == APP_NAME
    help_text = app.info.help or ''
    assert 'freight rail DAC migration simulation tool' in help_text
