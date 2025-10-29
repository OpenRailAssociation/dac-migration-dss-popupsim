"""Unit tests for the Routes class and related functions."""

from pathlib import Path
import tempfile

import pytest

from configuration.model_route import Route
from configuration.model_routes import Routes
from configuration.model_routes import load_routes_from_csv


@pytest.fixture
def routes_csv_path() -> Path:
    """Return the path to the test routes CSV file."""
    return Path(__file__).parent.parent / 'fixtures' / 'config' / 'routes.csv'


@pytest.fixture
def routes(routes_csv_path: Path) -> Routes:
    """Return a Routes instance with test data loaded."""
    return Routes(routes_csv_path)


@pytest.fixture
def temp_csv_file() -> Path:
    """Create a temporary CSV file with test route data."""
    # Create a temporary file
    return Path(tempfile.mkstemp(suffix='.csv')[1])


@pytest.mark.unit
class TestRoutes:
    """Test suite for Routes class."""

    def test_init_with_file(self, routes_csv_path: Path) -> None:
        """Test initialization with a file path."""
        routes = Routes(routes_csv_path)
        assert len(routes.routes) == 5
        assert len(routes.routes_by_id) == 5
        assert 'ROUTE01' in routes.routes_by_id

    def test_init_without_file(self) -> None:
        """Test initialization without a file path."""
        routes = Routes()
        assert routes.length == 0
        assert len(routes.routes_by_id) == 0

    def test_init_with_string_path(self, routes_csv_path: Path) -> None:
        """Test initialization with a string path."""
        routes = Routes(str(routes_csv_path))
        assert routes.length == 5

    def test_load_routes(self, routes_csv_path: Path) -> None:
        """Test loading routes from CSV."""
        routes = Routes()
        assert routes.length == 0

        routes.load_routes(routes_csv_path)
        assert routes.length == 5

        # Test that reload clears previous data
        routes.load_routes(routes_csv_path)
        assert routes.length == 5

    def test_load_nonexistent_file(self) -> None:
        """Test loading from a nonexistent file."""
        routes = Routes()
        with pytest.raises(FileNotFoundError, match='Routes file not found'):
            routes.load_routes('nonexistent_file.csv')

    def test_invalid_csv_format(self, tmp_path: Path) -> None:
        """Test loading from a CSV with missing required columns."""
        # Create a CSV file with missing columns
        invalid_csv = tmp_path / 'invalid.csv'
        invalid_csv.write_text('route_id,from_track\nROUTE01,track1')

        routes = Routes()
        with pytest.raises(ValueError, match='Missing required columns in CSV'):
            routes.load_routes(invalid_csv)

    def test_invalid_route_data(self, temp_csv_file: Path) -> None:
        """Test loading routes with invalid data."""
        # Create a CSV file with invalid route data (negative distance)
        temp_csv_file.write_text(
            'route_id;from_track;to_track;track_sequence;distance_m;time_min\n'
            'INVALID;track1;track2;"track1,track2";-100;5'
        )

        routes = Routes()
        with pytest.raises(ValueError, match='Error parsing route INVALID'):
            routes.load_routes(temp_csv_file)

    def test_get_route(self, routes: Routes) -> None:
        """Test getting a route by ID."""
        route = routes.get_route('ROUTE01')
        assert isinstance(route, Route)
        assert route.route_id == 'ROUTE01'
        assert route.from_track == 'sammelgleis'
        assert route.to_track == 'werkstattzufuehrung'

    def test_get_nonexistent_route(self, routes: Routes) -> None:
        """Test getting a nonexistent route."""
        with pytest.raises(KeyError, match='Route not found'):
            routes.get_route('NONEXISTENT')

    def test_get_route_between_tracks(self, routes: Routes) -> None:
        """Test finding a route between two tracks."""
        route = routes.get_route_between_tracks('sammelgleis', 'werkstattzufuehrung')
        assert route is not None
        assert route.route_id == 'ROUTE01'

    def test_get_nonexistent_route_between_tracks(self, routes: Routes) -> None:
        """Test finding a nonexistent route between tracks."""
        route = routes.get_route_between_tracks('nonexistent', 'track')
        assert route is None

    def test_iter_method(self, routes: Routes) -> None:
        """Test the __iter__ method."""
        assert routes.length == 5
        assert all(isinstance(route, Route) for route in routes)

    def test_csv_malformed_data(self, temp_csv_file: Path) -> None:
        """Test handling of malformed CSV data."""
        temp_csv_file.write_text('This is not a CSV file')

        routes = Routes()
        with pytest.raises(ValueError, match='Missing required columns in CSV'):
            routes.load_routes(temp_csv_file)


@pytest.mark.unit
class TestRoutesFromRoutes:
    """Test suite for loading Routes from an existing Routes instance."""

    def test_init_from_route(self) -> None:
        """Test initialization from an existing Routes instance."""
        route = Route(
            route_id='TEST01',
            from_track='track1',
            to_track='track2',
            track_sequence=['track1', 'middle', 'track2'],
            distance_m=100.5,
            time_min=5,
        )
        routes = Routes(routes=[route])
        assert routes.length == 1
        assert routes.routes_by_id['TEST01'] == route


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
