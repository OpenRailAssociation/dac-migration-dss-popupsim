"""Unit tests for the Routes class and related functions."""

from collections.abc import Generator
import json
from pathlib import Path
import tempfile

from models.route import Route
from models.routes import Routes
import pytest

len_test_routes = 3


@pytest.fixture
def routes_json_path() -> Path:
    """Return a Routes file path to be loaded."""
    temp_file = Path(tempfile.mkstemp(suffix='.json')[1])
    routes_data = {
        'metadata': {
            'description': 'Test Routes',
            'version': '1.0.0',
            'topology_reference': 'topology.yaml',
            'tracks_reference': 'tracks.yaml',
        },
        'routes': [
            {
                'id': '6_To_10',
                'description': 'Route from retrofit track to workshop 1',
                'duration': None,
                'path': ['track_6', 'track_1a', 'track_10'],
            },
            {
                'id': 'Tracktrack_6ToTracktrack_Z1',
                'description': 'Route from retrofit track to workshop 2',
                'path': ['track_6', 'track_1a', 'track_Z1'],
            },
            {
                'id': 'parking_to_10',
                'path': ['track_19', 'track_1a', 'track_10'],
            },
        ],
    }
    temp_file.write_text(json.dumps(routes_data))
    return temp_file


@pytest.fixture
def temp_json_file() -> Generator[Path]:
    """Create a temporary JSON file with test route data."""
    temp_file = Path(tempfile.mkstemp(suffix='.json')[1])
    yield temp_file
    if temp_file.exists():
        temp_file.unlink()


@pytest.mark.unit
class TestRoutes:
    """Test suite for Routes class."""

    def test_init_with_file(self, routes_json_path: Path) -> None:
        """Test initialization with a file path."""
        routes: Routes = Routes(routes_json_path)
        assert len(routes.routes) == len_test_routes
        assert len(routes.routes_by_id) == len_test_routes
        assert '6_To_10' in routes.routes_by_id

    def test_init_without_file(self) -> None:
        """Test initialization without a file path."""
        routes: Routes = Routes()
        assert routes.length == 0
        assert len(routes.routes_by_id) == 0

    def test_load_nonexistent_file(self) -> None:
        """Test loading from a nonexistent file."""
        routes: Routes = Routes()
        with pytest.raises(FileNotFoundError, match='Routes file not found'):
            routes.load_routes(Path('nonexistent_file.json'))

    def test_invalid_json_format(self, tmp_path: Path) -> None:
        """Test loading from an invalid JSON file."""
        invalid_json: Path = tmp_path / 'invalid.json'
        invalid_json.write_text('This is not valid JSON')

        routes: Routes = Routes()
        with pytest.raises(ValueError, match='Invalid JSON format'):
            routes.load_routes(invalid_json)

    def test_missing_routes_key(self, tmp_path: Path) -> None:
        """Test loading from JSON without 'routes' key."""
        invalid_json: Path = tmp_path / 'no_routes.json'
        invalid_json.write_text('{"metadata": {"version": "1.0"}}')

        routes: Routes = Routes()
        with pytest.raises(ValueError, match='validation errors for MetaData'):
            routes.load_routes(invalid_json)

    def test_invalid_route_data(self, temp_json_file: Path) -> None:
        """Test loading routes with invalid data."""
        routes_data = {
            'metadata': {
                'description': 'Test Routes',
                'version': '1.0.0',
                'topology_reference': 'topology.yaml',
                'tracks_reference': 'tracks.yaml',
            },
            'routes': [{'id': 'INVALID', 'path': ['single_track']}],
        }
        temp_json_file.write_text(json.dumps(routes_data))

        routes: Routes = Routes()
        with pytest.raises(ValueError, match='Error parsing route INVALID'):
            routes.load_routes(temp_json_file)

    def test_get_route(self, routes_json_path: Path) -> None:
        """Test getting a route by ID."""
        routes: Routes = Routes(routes_json_path)
        route: Route = routes.get_route('6_To_10')
        assert isinstance(route, Route)
        assert route.route_id == '6_To_10'
        assert route.from_track == 'track_6'
        assert route.to_track == 'track_10'
        assert route.path == ['track_6', 'track_1a', 'track_10']


@pytest.mark.unit
class TestRoutesFromRoutes:
    """Test suite for loading Routes from an existing Routes instance."""

    def test_init_from_route(self) -> None:
        """Test initialization from an existing Routes instance."""
        route: Route = Route(
            route_id='TEST01',
            path=['track_1', 'track_middle', 'track_2'],
            description='Test route',
            duration=5,
        )
        routes: Routes = Routes(routes=[route])
        assert routes.length == 1
        assert routes.routes_by_id['TEST01'] == route

    def test_init_from_multiple_routes(self) -> None:
        """Test initialization from multiple routes."""
        route1: Route = Route(
            route_id='TEST01',
            path=['track_1', 'track_2'],
        )
        route2: Route = Route(
            route_id='TEST02',
            path=['track_2', 'track_3'],
        )
        routes: Routes = Routes(routes=[route1, route2])
        assert routes.length == 2
        assert 'TEST01' in routes.routes_by_id
        assert 'TEST02' in routes.routes_by_id
