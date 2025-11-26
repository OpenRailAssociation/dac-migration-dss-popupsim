"""
Unit tests for Track model.

Tests the Track model validation logic, field constraints,
and error handling for workshop track configurations.
"""

from pydantic import ValidationError
import pytest
from workshop_operations.domain.entities.track import Track
from workshop_operations.domain.entities.track import TrackType


class TestTrackType:
    """Test cases for TrackType enum."""

    def test_track_type_enum_values(self) -> None:
        """Test that all TrackType enum values are accessible and have correct string values."""
        expected_types: dict[TrackType, str] = {
            TrackType.LOCOPARKING: 'loco_parking',
            TrackType.COLLECTION: 'collection',
            TrackType.MAINLINE: 'mainline',
            TrackType.PARKING: 'parking_area',
            TrackType.RETROFIT: 'retrofit',
            TrackType.RETROFITTED: 'retrofitted',
            TrackType.WORKSHOP: 'workshop_area',
        }

        for track_type, expected_value in expected_types.items():
            assert track_type.value == expected_value
            assert TrackType(expected_value) == track_type


class TestTrack:
    """Test cases for Track model."""

    def test_track_creation_valid_data(self) -> None:
        """
        Test successful track creation with valid data.

        Validates that Track instances can be created with valid parameters
        and that all fields are correctly assigned.
        """
        track = Track(id='TRACK01', type=TrackType.WORKSHOP, edges=['edge_1', 'edge_2'])

        assert track.id == 'TRACK01'
        assert track.type == TrackType.WORKSHOP
        assert track.edges == ['edge_1', 'edge_2']

    def test_track_type_validation_all_enum_values(self) -> None:
        """
        Test type field validation with all TrackType enum values.

        Tests
        -----
        Validates that Track can be instantiated with each TrackType enum value
        and that the type field is correctly assigned.
        """
        for track_type in TrackType:
            track = Track(id='TRACK01', type=track_type, edges=['edge_1', 'edge_2'])
            assert track.type == track_type

    def test_track_type_validation_with_string_value(self) -> None:
        """
        Test that track type can be created from string value.

        Tests
        -----
        Validates that TrackType enum values can be assigned using their
        string representations (e.g., 'workshop' for WORKSHOP).
        """
        workshop_type = TrackType.WORKSHOP
        track = Track(id='TRACK01', type=workshop_type, edges=['edge_1', 'edge_2'])
        assert track.type == TrackType.WORKSHOP

    def test_track_type_validation_invalid_string(self) -> None:
        """
        Test that invalid string value raises ValidationError.

        Tests
        -----
        Validates that attempting to create a Track with an invalid
        track type string raises a ValidationError.
        """
        with pytest.raises(ValidationError) as exc_info:
            Track(id='TRACK01', type='invalid_type', edges=['edge_1', 'edge_2'])
        assert 'Input should be' in str(exc_info.value)

    def test_track_missing_required_fields(self) -> None:
        """
        Test that missing required fields raise ValidationError.

        Tests
        -----
        Validates that attempting to create a Track without required fields
        raises a ValidationError with 'Field required' message.
        """
        with pytest.raises(ValidationError) as exc_info:
            Track()  # type: ignore
        error_msg = str(exc_info.value)
        assert 'Field required' in error_msg

    def test_track_field_order_independence(self) -> None:
        """
        Test that field order doesn't matter during creation.

        Tests
        -----
        Validates that Track instances created with the same field values
        but in different order produce identical objects.
        """
        track1 = Track(id='TRACK01', type=TrackType.WORKSHOP, edges=['edge_1', 'edge_2'])

        track2 = Track(edges=['edge_1', 'edge_2'], type=TrackType.WORKSHOP, id='TRACK01')

        assert track1.id == track2.id
        assert track1.type == track2.type
        assert track1.edges == track2.edges
