"""Unit tests for the Route model."""

import pytest

from configuration.model_route import Route


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

    def test_parse_track_sequence_with_spaces(self) -> None:
        """Test that track_sequence can be parsed from string with spaces."""
        route = Route(
            route_id='TEST02',
            from_track='track1',
            to_track='track2',
            track_sequence='  track1 , middle , track2  ',
            distance_m=100.5,
            time_min=5,
        )

        assert isinstance(route.track_sequence, list)
        assert route.track_sequence == ['track1', 'middle', 'track2']

    def test_parse_track_sequence_track_sequence_must_be_list(self) -> None:
        """Test that track_sequence can be parsed from single-quoted string."""
        with pytest.raises(ValueError, match='track_sequence must be a list or a comma-separated string'):
            Route(
                route_id='TEST03',
                from_track='track1',
                to_track='track2',
                track_sequence=' track1 middle track2',
                distance_m=100.5,
                time_min=5,
            )

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

    def test_parse_track_sequence_with_dict_containing_dict(self) -> None:
        """Test track_sequence parsing when data contains nested dict.

        This tests the edge case where the validator receives a dict with
        'track_sequence' as a nested dict instead of a string or list.
        The validator should handle this gracefully by returning data as-is.
        """
        with pytest.raises(ValueError, match='Input should be a valid list'):
            Route(
                route_id='TEST001',
                from_track='track1',
                to_track='track3',
                track_sequence={'nested': 'dict'},  # Invalid nested structure
                distance_m=1000.0,
                time_min=10,
            )

    def test_parse_track_sequence_dict_with_list(self) -> None:
        """Test track_sequence parsing when dict contains list.

        When the validator receives a dict with 'track_sequence' as a list,
        it should process the list correctly and assign it to parsed_sequence.

        Notes
        -----
        This covers the case at line 58 where track_sequence is already a list
        within the dict structure, requiring assignment to parsed_sequence.
        """
        track_list: list[str] = ['track1', 'track2', 'track3']

        route: Route = Route(
            route_id='TEST002',
            from_track='track1',
            to_track='track3',
            track_sequence=track_list,
            distance_m=1000.0,
            time_min=10,
        )

        assert route.track_sequence == track_list
        assert len(route.track_sequence) == 3

    def test_parse_track_sequence_dict_with_string(self) -> None:
        """Test track_sequence parsing when dict contains comma-separated string.

        When the validator receives a dict with 'track_sequence' as a
        comma-separated string, it should parse and validate the string
        into a list of track identifiers.

        Notes
        -----
        This covers the string parsing branch at line 63 where CSV-formatted
        track sequences are converted to lists and validated for string types.
        """
        route: Route = Route(
            route_id='TEST003',
            from_track='track1',
            to_track='track3',
            track_sequence='"track1,track2,track3"',  # CSV-style quoted string
            distance_m=1500.0,
            time_min=15,
        )

        assert route.track_sequence == ['track1', 'track2', 'track3']
        assert len(route.track_sequence) == 3
