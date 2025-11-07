"""
Unit tests for Track model.

Tests the Track model validation logic, field constraints,
and error handling for workshop track configurations.
"""

from pydantic import ValidationError
import pytest

from configuration.model_track import Track
from configuration.model_track import TrackType


class TestTrackType:
    """Test cases for TrackType enum."""

    def test_track_type_enum_values(self) -> None:
        """Test that all TrackType enum values are accessible."""
        assert TrackType.WERKSTATTGLEIS.value == 'workshop'
        assert TrackType.SAMMELGLEIS.value == 'collection'
        assert TrackType.PARKGLEIS.value == 'parking'
        assert TrackType.WERKSTATTZUFUEHRUNG.value == 'to_be_retroffitted'
        assert TrackType.WERKSTATTABFUEHRUNG.value == 'retrofitted'
        assert TrackType.BAHNHOFSKOPF_1.value == 'station_head_1'
        assert TrackType.BAHNHOFSKOPF_N.value == 'station_head_n'
        assert TrackType.CIRCULATING_TRACK.value == 'circulating_track'
        assert TrackType.DISPENSER.value == 'dispenser'
        assert TrackType.DISPENSER_2_CONTROL.value == 'dispenser_2_control'
        assert TrackType.TO_PARKING_CONTROL.value == 'to_parking_control'
        assert TrackType.SELECTOR.value == 'selector'

    def test_track_type_enum_count(self) -> None:
        """Test that TrackType enum has expected number of members."""
        assert len(TrackType) == 12


class TestTrack:
    """Test cases for Track model."""

    def test_track_creation_valid_data(self) -> None:
        """Test successful track creation with valid data."""
        track = Track(id='TRACK01', length=500.0, type=TrackType.WERKSTATTGLEIS, sh_1=1, sh_n=2)

        assert track.id == 'TRACK01'
        assert track.length == 500.0
        assert track.type == TrackType.WERKSTATTGLEIS
        assert track.sh_1 == 1
        assert track.sh_n == 2

        track = Track(id='TRACK01', length=10.0, type=TrackType.SAMMELGLEIS)

    def test_track_length_validation_valid_values(self) -> None:
        """Test length validation with valid positive values."""
        valid_lengths = [0.1, 1.0, 100.5, 500.0, 1000.0, 9999.99]

        for length in valid_lengths:
            track = Track(id='TRACK01', length=length, type=TrackType.WERKSTATTGLEIS, sh_1=0, sh_n=0)
            assert track.length == length

    def test_track_length_validation_invalid_values(self) -> None:
        """Test length validation with invalid values."""
        invalid_lengths = [0, -0.1, -1.0, -100.0]

        for length in invalid_lengths:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', length=length, type=TrackType.WERKSTATTGLEIS, sh_1=0, sh_n=0)
            assert 'greater than 0' in str(exc_info.value)

    def test_track_type_validation_all_enum_values(self) -> None:
        """Test type field validation with all TrackType enum values."""
        for track_type in TrackType:
            track = Track(id='TRACK01', length=100.0, type=track_type, sh_1=0, sh_n=0)
            assert track.type == track_type

    def test_track_sh_1_validation_valid_values(self) -> None:
        """Test sh_1 validation with valid non-negative values."""
        valid_values = [0, 1, 5, 10, 100, 999]

        for sh_1_value in valid_values:
            track = Track(id='TRACK01', length=100.0, type=TrackType.WERKSTATTGLEIS, sh_1=sh_1_value, sh_n=0)
            assert track.sh_1 == sh_1_value

    def test_track_sh_1_validation_invalid_values(self) -> None:
        """Test sh_1 validation with invalid negative values."""
        invalid_values = [-1, -5, -100]

        for sh_1_value in invalid_values:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', length=100.0, type=TrackType.WERKSTATTGLEIS, sh_1=sh_1_value, sh_n=0)
            assert 'greater than or equal to 0' in str(exc_info.value)

    def test_track_sh_n_validation_valid_values(self) -> None:
        """Test sh_n validation with valid non-negative values."""
        valid_values = [0, 1, 5, 10, 100, 999]

        for sh_n_value in valid_values:
            track = Track(id='TRACK01', length=100.0, type=TrackType.WERKSTATTGLEIS, sh_1=0, sh_n=sh_n_value)
            assert track.sh_n == sh_n_value

    def test_track_sh_n_validation_invalid_values(self) -> None:
        """Test sh_n validation with invalid negative values."""
        invalid_values = [-1, -5, -100]

        for sh_n_value in invalid_values:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', length=100.0, type=TrackType.WERKSTATTGLEIS, sh_1=0, sh_n=sh_n_value)
            assert 'greater than or equal to 0' in str(exc_info.value)

    def test_track_type_validation_with_string_value(self) -> None:
        """Test that track type can be created from string value."""
        track = Track(id='TRACK01', length=100.0, type='workshop', sh_1=0, sh_n=0)
        assert track.type == TrackType.WERKSTATTGLEIS

    def test_track_type_validation_invalid_string(self) -> None:
        """Test that invalid string value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Track(id='TRACK01', length=100.0, type='invalid_type', sh_1=0, sh_n=0)
        assert 'Input should be' in str(exc_info.value)

    def test_track_creation_with_different_track_types(self) -> None:
        """Test track creation with different track types."""
        test_cases = [
            (TrackType.WERKSTATTGLEIS, 'workshop'),
            (TrackType.SAMMELGLEIS, 'collection'),
            (TrackType.PARKGLEIS, 'parking'),
            (TrackType.WERKSTATTZUFUEHRUNG, 'to_be_retroffitted'),
            (TrackType.WERKSTATTABFUEHRUNG, 'retrofitted'),
            (TrackType.BAHNHOFSKOPF_1, 'station_head_1'),
            (TrackType.BAHNHOFSKOPF_N, 'station_head_n'),
            (TrackType.CIRCULATING_TRACK, 'circulating_track'),
            (TrackType.DISPENSER, 'dispenser'),
            (TrackType.DISPENSER_2_CONTROL, 'dispenser_2_control'),
            (TrackType.TO_PARKING_CONTROL, 'to_parking_control'),
            (TrackType.SELECTOR, 'selector'),
        ]

        for track_type, expected_value in test_cases:
            track = Track(id='TRACK01', length=100.0, type=track_type, sh_1=1, sh_n=2)
            assert track.type == track_type
            assert track.type.value == expected_value

    def test_track_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Track()  # type: ignore
        error_msg = str(exc_info.value)
        assert 'Field required' in error_msg

    def test_track_field_order_independence(self) -> None:
        """Test that field order doesn't matter during creation."""
        track1 = Track(id='TRACK01', length=100.0, type=TrackType.WERKSTATTGLEIS, sh_1=1, sh_n=2)

        track2 = Track(sh_n=2, sh_1=1, type=TrackType.WERKSTATTGLEIS, length=100.0, id='TRACK01')

        assert track1.id == track2.id
        assert track1.length == track2.length
        assert track1.type == track2.type
        assert track1.sh_1 == track2.sh_1
        assert track1.sh_n == track2.sh_n
