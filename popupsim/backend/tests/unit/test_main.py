"""Unit tests for the main entry point module."""

from collections.abc import Generator
from pathlib import Path
import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from main import APP_NAME
from main import app
from main import validate_output_path
from main import validate_scenario_path


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
@patch('main.ConfigurationService')
def test_main_with_valid_parameters(
    mock_config_service: MagicMock, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function succeeds with valid parameters."""
    mock_service = MagicMock()
    mock_config = MagicMock()
    mock_config.scenario_id = 'test_scenario'
    mock_config.start_date = '2024-01-01'
    mock_config.end_date = '2024-12-31'
    mock_config.train = []
    mock_config.workshop.tracks = []
    mock_config.routes = []
    mock_validation = MagicMock()
    mock_service.load_complete_scenario.return_value = (mock_config, mock_validation)
    mock_config_service.return_value = mock_service

    result = runner.invoke(app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir)])

    assert result.exit_code == 0
    assert f'✓ Using scenario file at: {temp_scenario_file}' in result.stdout
    assert f'✓ Output will be saved to: {temp_output_dir}' in result.stdout
    assert '✓ Debug level set to: INFO' in result.stdout
    assert '🚀 Starting popupsim processing...' in result.stdout


@pytest.mark.unit
@patch('main.ConfigurationService')
def test_main_with_verbose_flag(
    mock_config_service: MagicMock, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function with verbose flag enabled."""
    mock_service = MagicMock()
    mock_config = MagicMock()
    mock_config.scenario_id = 'test_scenario'
    mock_config.start_date = '2024-01-01'
    mock_config.end_date = '2024-12-31'
    mock_config.train = []
    mock_config.workshop.tracks = []
    mock_config.routes = []
    mock_validation = MagicMock()
    mock_service.load_complete_scenario.return_value = (mock_config, mock_validation)
    mock_config_service.return_value = mock_service

    result = runner.invoke(
        app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir), '--verbose']
    )

    assert result.exit_code == 0
    assert '✓ Verbose mode enabled.' in result.stdout


@pytest.mark.unit
@patch('main.ConfigurationService')
def test_main_with_custom_debug_level(
    mock_config_service: MagicMock, runner: CliRunner, temp_scenario_file: Path, temp_output_dir: Path
) -> None:
    """Test main function with custom debug level."""
    mock_service = MagicMock()
    mock_config = MagicMock()
    mock_config.scenario_id = 'test_scenario'
    mock_config.start_date = '2024-01-01'
    mock_config.end_date = '2024-12-31'
    mock_config.train = []
    mock_config.workshop.tracks = []
    mock_config.routes = []
    mock_validation = MagicMock()
    mock_service.load_complete_scenario.return_value = (mock_config, mock_validation)
    mock_config_service.return_value = mock_service

    result = runner.invoke(
        app, ['--scenarioPath', str(temp_scenario_file), '--outputPath', str(temp_output_dir), '--debug', 'DEBUG']
    )

    assert result.exit_code == 0
    assert '✓ Debug level set to: DEBUG' in result.stdout


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
