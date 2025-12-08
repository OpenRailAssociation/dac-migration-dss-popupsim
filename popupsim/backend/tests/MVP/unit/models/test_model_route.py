"""Unit tests for the Route model."""

import pytest

from popupsim.backend.src.MVP.workshop_operations.domain.value_objects.route import (
    Route,
)


@pytest.mark.unit
class TestRoute:
    """Test suite for Route model validation and methods."""

    def test_route_initialization_with_id_alias(self) -> None:
        """Test that a Route can be created using 'id' field."""
        route: Route = Route(
            id="TEST01",
            path=["track_6", "track_1a", "track_10"],
            description="Test route from track 6 to track 10",
            duration=5,
        )

        assert route.route_id == "TEST01"
        assert route.path == ["track_6", "track_1a", "track_10"]
        assert route.description == "Test route from track 6 to track 10"
        assert route.duration == 5

    def test_route_initialization_with_route_id(self) -> None:
        """Test that a Route can be created using 'route_id' field."""
        route: Route = Route(
            route_id="TEST02",
            path=["track_7", "track_1a", "track_19"],
            description="Test route",
        )

        assert route.route_id == "TEST02"
        assert route.path == ["track_7", "track_1a", "track_19"]

    def test_route_minimal_required_fields(self) -> None:
        """Test that a Route can be created with minimal required fields."""
        route: Route = Route(
            id="TEST03",
            path=["track_10", "track_1a", "track_7"],
        )

        assert route.route_id == "TEST03"
        assert route.path == ["track_10", "track_1a", "track_7"]
        assert route.description is None
        assert route.duration is None

    def test_from_track_property(self) -> None:
        """Test that from_track property returns first track in path."""
        route: Route = Route(
            id="TEST04",
            path=["track_6", "track_1a", "track_Z1"],
        )

        assert route.from_track == "track_6"

    def test_to_track_property(self) -> None:
        """Test that to_track property returns last track in path."""
        route: Route = Route(
            id="TEST05",
            path=["track_Z1", "track_1a", "track_7"],
        )

        assert route.to_track == "track_7"

    def test_track_sequence_property(self) -> None:
        """Test that track_sequence property returns complete path."""
        route: Route = Route(
            id="TEST06",
            path=["track_7", "track_1a", "track_9"],
        )

        assert route.track_sequence == ["track_7", "track_1a", "track_9"]
        assert route.track_sequence is route.path

    def test_parse_path_from_string(self) -> None:
        """Test that path can be parsed from comma-separated string."""
        route: Route = Route(
            id="TEST07",
            path="track_10,track_1a,track_19",
        )

        assert isinstance(route.path, list)
        assert route.path == ["track_10", "track_1a", "track_19"]

    def test_parse_path_with_spaces(self) -> None:
        """Test that path can be parsed from string with spaces."""
        route: Route = Route(
            id="TEST08",
            path="  track_9 , track_1a , track_19  ",
        )

        assert isinstance(route.path, list)
        assert route.path == ["track_9", "track_1a", "track_19"]

    def test_parse_path_with_quotes(self) -> None:
        """Test that path can be parsed from quoted string."""
        route: Route = Route(
            id="TEST09",
            path='"track_24,track_1a,track_19"',
        )

        assert isinstance(route.path, list)
        assert route.path == ["track_24", "track_1a", "track_19"]

    def test_parse_path_with_single_quotes(self) -> None:
        """Test that path can be parsed from single-quoted string."""
        route: Route = Route(
            id="TEST10",
            path="'track_23,track_1a,track_19'",
        )

        assert isinstance(route.path, list)
        assert route.path == ["track_23", "track_1a", "track_19"]

    def test_already_list_path(self) -> None:
        """Test that path is preserved if already a list."""
        track_list: list[str] = ["track_7", "track_1a", "track_19"]
        route: Route = Route(
            id="TEST11",
            path=track_list,
        )

        assert route.path == track_list

    def test_validate_empty_path(self) -> None:
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="must have a valid path"):
            Route(
                id="INVALID01",
                path=[],
            )

    def test_validate_empty_string_path(self) -> None:
        """Test that empty string path raises ValueError."""
        with pytest.raises(ValueError, match="path cannot be an empty string"):
            Route(
                id="INVALID02",
                path="",
            )

    def test_validate_whitespace_only_path(self) -> None:
        """Test that whitespace-only path raises ValueError."""
        with pytest.raises(ValueError, match="path cannot be an empty string"):
            Route(
                id="INVALID03",
                path="   ",
            )

    def test_validate_short_path(self) -> None:
        """Test that path with less than 2 tracks raises ValueError."""
        with pytest.raises(ValueError, match="must have at least two tracks in path"):
            Route(
                id="INVALID04",
                path=["only_one"],
            )

    def test_parse_path_invalid_type(self) -> None:
        """Test that invalid path type raises ValueError."""
        with pytest.raises(
            ValueError, match="path must be a list or comma-separated string"
        ):
            Route(
                id="INVALID05",
                path=123,  # type: ignore[arg-type]
            )

    def test_parse_path_dict_type(self) -> None:
        """Test that dict path type raises ValueError."""
        with pytest.raises(
            ValueError, match="path must be a list or comma-separated string"
        ):
            Route(
                id="INVALID06",
                path={"nested": "dict"},  # type: ignore[arg-type]
            )

    def test_route_from_json_structure(self) -> None:
        """Test that Route can be created from JSON-like dict."""
        route_data: dict[str, object] = {
            "id": "6_To_10",
            "description": "Route from retrofit track to workshop 1",
            "duration": None,
            "path": ["track_6", "track_1a", "track_10"],
        }

        route: Route = Route(**route_data)

        assert route.route_id == "6_To_10"
        assert route.path == ["track_6", "track_1a", "track_10"]
        assert route.description == "Route from retrofit track to workshop 1"
        assert route.duration is None
        assert route.from_track == "track_6"
        assert route.to_track == "track_10"

    def test_multiple_routes_from_json_example(self) -> None:
        """Test creating multiple routes matching the routes.json structure."""
        routes_data: list[dict[str, object]] = [
            {
                "id": "6_To_10",
                "description": "Route from retrofit track to workshop 1",
                "duration": None,
                "path": ["track_6", "track_1a", "track_10"],
            },
            {
                "id": "Tracktrack_6ToTracktrack_Z1",
                "description": "Route from retrofit track to workshop 2",
                "path": ["track_6", "track_1a", "track_Z1"],
            },
            {
                "id": "parking_to_10",
                "path": ["track_19", "track_1a", "track_10"],
            },
        ]

        routes: list[Route] = [Route(**data) for data in routes_data]

        assert len(routes) == 3
        assert routes[0].route_id == "6_To_10"
        assert routes[0].from_track == "track_6"
        assert routes[0].to_track == "track_10"
        assert routes[1].from_track == "track_6"
        assert routes[1].to_track == "track_Z1"
        assert routes[2].description is None
        assert routes[2].duration is None
