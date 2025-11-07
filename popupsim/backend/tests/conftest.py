"""Configure pytest to find the src package."""

from pathlib import Path

import pytest

# Pytest configuration - mypy_path in pyproject.toml handles module resolution


@pytest.fixture
def fixtures_config_path() -> Path:
    """Provide path to test configuration fixtures directory.

    Returns
    -------
    Path
        Path to popupsim/backend/tests/fixtures/config directory.

    Examples
    --------
    >>> def test_something(fixtures_config_path: Path) -> None:
    ...     scenario_file = fixtures_config_path / 'test_scenario.json'
    ...     assert scenario_file.exists()
    """
    return Path(__file__).parent / 'fixtures' / 'config'


@pytest.fixture
def test_scenario_json_path(fixtures_config_path: Path) -> Path:
    """Provide path to the test scenario JSON file.

    Returns
    -------
    Path
        Path to test_scenario.json file.

    Examples
    --------
    >>> def test_load_scenario(test_scenario_json_path: Path) -> None:
    ...     assert test_scenario_json_path.exists()
    ...     assert test_scenario_json_path.name == 'test_scenario.json'
    """
    return fixtures_config_path / 'test_scenario.json'


@pytest.fixture
def routes_csv_path(fixtures_config_path: Path) -> Path:
    """Return the path to the test routes CSV file."""
    return fixtures_config_path / 'test_routes.csv'
