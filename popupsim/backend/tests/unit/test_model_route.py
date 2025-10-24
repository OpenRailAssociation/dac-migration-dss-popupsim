"""Unit tests for the Route model."""

import pytest

from src.configuration.model_route import Route


@pytest.mark.unit
class TestRoute:
    """Test suite for Route model validation and methods."""

    def test_route_initialization(self) -> None:
        """Test that a Route can be created with valid data."""
        route = Route(
            route_id='TEST01',
            from_track='track1',
            to_track='track2',
            track_sequence=['track1', 'middle', 'track2'],
            distance_m=100.5,
            time_min=5,
        )

        assert route.route_id == 'TEST01'
        assert route.from_track == 'track1'
        assert route.to_track == 'track2'
        assert route.track_sequence == ['track1', 'middle', 'track2']
        assert route.distance_m == 100.5
        assert route.time_min == 5

    def test_parse_track_sequence_from_string(self) -> None:
        """Test that track_sequence can be parsed from string."""
        route = Route(
            route_id='TEST02',
            from_track='track1',
            to_track='track2',
            track_sequence='track1,middle,track2',
            distance_m=100.5,
            time_min=5,
        )

        assert isinstance(route.track_sequence, list)
        assert route.track_sequence == ['track1', 'middle', 'track2']

    def test_parse_track_sequence_with_quotes(self) -> None:
        """Test that track_sequence can be parsed from quoted string."""
        route = Route(
            route_id='TEST03',
            from_track='track1',
            to_track='track2',
            track_sequence='"track1,middle,track2"',
            distance_m=100.5,
            time_min=5,
        )

        assert isinstance(route.track_sequence, list)
        assert route.track_sequence == ['track1', 'middle', 'track2']

    def test_already_list_track_sequence(self) -> None:
        """Test that track_sequence is preserved if already a list."""
        track_list = ['track1', 'middle', 'track2']
        route = Route(
            route_id='TEST04',
            from_track='track1',
            to_track='track2',
            track_sequence=track_list,
            distance_m=100.5,
            time_min=5,
        )

        assert route.track_sequence is not track_list  # Pydantic creates a new list
        assert route.track_sequence == track_list

    def test_validate_empty_track_sequence(self) -> None:
        """Test that empty track_sequence raises ValueError."""
        with pytest.raises(ValueError, match='must have a valid track_sequence'):
            Route(
                route_id='INVALID01',
                from_track='track1',
                to_track='track2',
                track_sequence=[],
                distance_m=100.5,
                time_min=5,
            )

    def test_validate_short_track_sequence(self) -> None:
        """Test that track_sequence with less than 2 tracks raises ValueError."""
        with pytest.raises(ValueError, match='must have at least two tracks in sequence'):
            Route(
                route_id='INVALID02',
                from_track='track1',
                to_track='track2',
                track_sequence=['only_one'],
                distance_m=100.5,
                time_min=5,
            )

    def test_validate_from_track_not_in_sequence(self) -> None:
        """Test that from_track must be in track_sequence."""
        with pytest.raises(ValueError, match='must include from_track'):
            Route(
                route_id='INVALID03',
                from_track='not_included',
                to_track='track2',
                track_sequence=['track1', 'middle', 'track2'],
                distance_m=100.5,
                time_min=5,
            )

    def test_validate_to_track_not_in_sequence(self) -> None:
        """Test that to_track must be in track_sequence."""
        with pytest.raises(ValueError, match='must include to_track'):
            Route(
                route_id='INVALID04',
                from_track='track1',
                to_track='not_included',
                track_sequence=['track1', 'middle', 'track3'],
                distance_m=100.5,
                time_min=5,
            )

    def test_negative_distance_validation(self) -> None:
        """Test that negative distance_m raises validation error."""
        with pytest.raises(ValueError, match='distance_m'):
            Route(
                route_id='INVALID05',
                from_track='track1',
                to_track='track2',
                track_sequence=['track1', 'track2'],
                distance_m=-50,
                time_min=5,
            )

    def test_zero_distance_validation(self) -> None:
        """Test that zero distance_m raises validation error."""
        with pytest.raises(ValueError, match='distance_m'):
            Route(
                route_id='INVALID06',
                from_track='track1',
                to_track='track2',
                track_sequence=['track1', 'track2'],
                distance_m=0,
                time_min=5,
            )

    def test_negative_time_validation(self) -> None:
        """Test that negative time_min raises validation error."""
        with pytest.raises(ValueError, match='time_min'):
            Route(
                route_id='INVALID07',
                from_track='track1',
                to_track='track2',
                track_sequence=['track1', 'track2'],
                distance_m=100,
                time_min=-2,
            )

    def test_zero_time_validation(self) -> None:
        """Test that zero time_min raises validation error."""
        with pytest.raises(ValueError, match='time_min'):
            Route(
                route_id='INVALID08',
                from_track='track1',
                to_track='track2',
                track_sequence=['track1', 'track2'],
                distance_m=100,
                time_min=0,
            )
