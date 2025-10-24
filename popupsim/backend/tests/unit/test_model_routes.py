"""Unit tests for the RoutesConfig class and related functions."""

import tempfile
from pathlib import Path

import pytest

from src.configuration.model_route import Route
from src.configuration.model_routes import RoutesConfig, load_routes_from_csv


@pytest.fixture
def routes_csv_path() -> Path:
    """Return the path to the test routes CSV file."""
    return Path(__file__).parent.parent / 'fixtures' / 'config' / 'routes.csv'


@pytest.fixture
def routes_config(routes_csv_path: Path) -> RoutesConfig:
    """Return a RoutesConfig instance with test data loaded."""
    return RoutesConfig(routes_csv_path)


@pytest.fixture
def temp_csv_file() -> Path:
    """Create a temporary CSV file with test route data."""
    # Create a temporary file
    return Path(tempfile.mkstemp(suffix='.csv')[1])


@pytest.mark.unit
class TestRoutesConfig:
    """Test suite for RoutesConfig class."""

    def test_init_with_file(self, routes_csv_path: Path) -> None:
        """Test initialization with a file path."""
        config = RoutesConfig(routes_csv_path)
        assert len(config.routes) == 5
        assert len(config.routes_by_id) == 5
        assert 'ROUTE01' in config.routes_by_id

    def test_init_without_file(self) -> None:
        """Test initialization without a file path."""
        config = RoutesConfig()
        assert len(config.routes) == 0
        assert len(config.routes_by_id) == 0

    def test_init_with_string_path(self, routes_csv_path: Path) -> None:
        """Test initialization with a string path."""
        config = RoutesConfig(str(routes_csv_path))
        assert len(config.routes) == 5

    def test_load_routes(self, routes_csv_path: Path) -> None:
        """Test loading routes from CSV."""
        config = RoutesConfig()
        assert len(config.routes) == 0

        config.load_routes(routes_csv_path)
        assert len(config.routes) == 5

        # Test that reload clears previous data
        config.load_routes(routes_csv_path)
        assert len(config.routes) == 5

    def test_load_nonexistent_file(self) -> None:
        """Test loading from a nonexistent file."""
        config = RoutesConfig()
        with pytest.raises(FileNotFoundError, match='Routes file not found'):
            config.load_routes('nonexistent_file.csv')

    def test_invalid_csv_format(self, tmp_path: Path) -> None:
        """Test loading from a CSV with missing required columns."""
        # Create a CSV file with missing columns
        invalid_csv = tmp_path / 'invalid.csv'
        invalid_csv.write_text('route_id,from_track\nROUTE01,track1')

        config = RoutesConfig()
        with pytest.raises(ValueError, match='Missing required columns in CSV'):
            config.load_routes(invalid_csv)

    def test_invalid_route_data(self, temp_csv_file: Path) -> None:
        """Test loading routes with invalid data."""
        # Create a CSV file with invalid route data (negative distance)
        temp_csv_file.write_text(
            'route_id;from_track;to_track;track_sequence;distance_m;time_min\n'
            'INVALID;track1;track2;"track1,track2";-100;5'
        )

        config = RoutesConfig()
        with pytest.raises(ValueError, match='Error parsing route INVALID'):
            config.load_routes(temp_csv_file)

    def test_get_route(self, routes_config: RoutesConfig) -> None:
        """Test getting a route by ID."""
        route = routes_config.get_route('ROUTE01')
        assert isinstance(route, Route)
        assert route.route_id == 'ROUTE01'
        assert route.from_track == 'sammelgleis'
        assert route.to_track == 'werkstattzufuehrung'

    def test_get_nonexistent_route(self, routes_config: RoutesConfig) -> None:
        """Test getting a nonexistent route."""
        with pytest.raises(KeyError, match='Route not found'):
            routes_config.get_route('NONEXISTENT')

    def test_get_route_between_tracks(self, routes_config: RoutesConfig) -> None:
        """Test finding a route between two tracks."""
        route = routes_config.get_route_between_tracks('sammelgleis', 'werkstattzufuehrung')
        assert route is not None
        assert route.route_id == 'ROUTE01'

    def test_get_nonexistent_route_between_tracks(self, routes_config: RoutesConfig) -> None:
        """Test finding a nonexistent route between tracks."""
        route = routes_config.get_route_between_tracks('nonexistent', 'track')
        assert route is None

    def test_len_method(self, routes_config: RoutesConfig) -> None:
        """Test the __len__ method."""
        assert len(routes_config) == 5

    def test_iter_method(self, routes_config: RoutesConfig) -> None:
        """Test the __iter__ method."""
        routes = list(routes_config)
        assert len(routes) == 5
        assert all(isinstance(route, Route) for route in routes)

    def test_csv_malformed_data(self, temp_csv_file: Path) -> None:
        """Test handling of malformed CSV data."""
        temp_csv_file.write_text('This is not a CSV file')

        config = RoutesConfig()
        with pytest.raises(ValueError, match='Missing required columns in CSV'):
            config.load_routes(temp_csv_file)


@pytest.mark.unit
class TestLoadRoutesFromCSV:
    """Test suite for the load_routes_from_csv function."""

    def test_load_routes_from_csv(self, routes_csv_path: Path) -> None:
        """Test loading routes from CSV using the convenience function."""
        routes = load_routes_from_csv(routes_csv_path)
        assert isinstance(routes, list)
        assert len(routes) == 5
        assert all(isinstance(route, Route) for route in routes)

    def test_load_routes_from_nonexistent_file(self) -> None:
        """Test loading from a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_routes_from_csv('nonexistent_file.csv')

    def test_load_routes_with_string_path(self, routes_csv_path: Path) -> None:
        """Test loading using a string path."""
        routes = load_routes_from_csv(str(routes_csv_path))
        assert len(routes) == 5
