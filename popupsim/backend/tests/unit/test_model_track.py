"""
Unit tests for Track model.

Tests the Track model validation logic, field constraints,
and error handling for workshop track configurations.
"""

import pytest
from pydantic import ValidationError

from src.configuration.model_track import Track


class TestTrack:
    """Test cases for Track model."""

    def test_track_creation_valid_data(self):
        """Test successful track creation with valid data."""
        track = Track(id='TRACK01', capacity=5, retrofit_time_min=30)

        assert track.id == 'TRACK01'
        assert track.capacity == 5
        assert track.retrofit_time_min == 30

    def test_track_id_validation_valid_formats(self):
        """Test track ID validation with various valid formats."""
        valid_ids = [
            'TRACK01',
            'track-02',
            'Track_03',
            'T1',
            'a',
            'A-B_C1',
            '12345',
            'T' * 20,  # Max length
        ]

        for track_id in valid_ids:
            track = Track(id=track_id, capacity=1, retrofit_time_min=1)
            assert track.id == track_id

    def test_track_id_validation_invalid_formats(self):
        """Test track ID validation with invalid formats."""
        invalid_ids = [
            '',  # Empty string
            ' ',  # Space
            'TRACK 01',  # Space in middle
            'TRACK@01',  # Special character
            'TRACK.01',  # Dot
            'TRACK#01',  # Hash
            'T' * 21,  # Too long (max 20 chars)
            'TRACK/01',  # Slash
            'TRACK+01',  # Plus
        ]

        for track_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                Track(id=track_id, capacity=1, retrofit_time_min=1)
            assert (
                'String should match pattern' in str(exc_info.value)
                or 'at least 1 character' in str(exc_info.value)
                or 'at most 20 characters' in str(exc_info.value)
            )

    def test_track_capacity_validation_valid_values(self):
        """Test capacity validation with valid positive values."""
        valid_capacities = [1, 5, 10, 100, 999]

        for capacity in valid_capacities:
            track = Track(id='TRACK01', capacity=capacity, retrofit_time_min=30)
            assert track.capacity == capacity

    def test_track_capacity_validation_invalid_values(self):
        """Test capacity validation with invalid values."""
        invalid_capacities = [0, -1, -10]

        for capacity in invalid_capacities:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=capacity, retrofit_time_min=30)
            assert 'greater than 0' in str(exc_info.value)

    def test_track_capacity_validation_non_integer(self):
        """Test capacity validation with non-integer values."""
        # Pydantic converts some values successfully, so we split into convertible and non-convertible

        # Test values that Pydantic can convert to integers
        convertible_values = [
            ('5', 5),  # string to int
            (1.0, 1),  # float without fractional part
        ]

        for input_val, expected_val in convertible_values:
            track = Track(id='TRACK01', capacity=input_val, retrofit_time_min=30)
            assert track.capacity == expected_val
            assert isinstance(track.capacity, int)

        # Test values that should raise ValidationError (floats with fractional parts)
        invalid_fractional = [1.5, 2.7]
        for capacity in invalid_fractional:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=capacity, retrofit_time_min=30)
            error_msg = str(exc_info.value)
            assert 'got a number with a fractional part' in error_msg

        # Test values that cannot be converted at all
        non_convertible = [None, [], {}, 'abc']
        for capacity in non_convertible:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=capacity, retrofit_time_min=30)
            error_msg = str(exc_info.value)
            assert (
                'Input should be a valid integer' in error_msg
                or 'greater than 0' in error_msg
                or 'Field required' in error_msg
            )

    def test_track_retrofit_time_validation_valid_values(self):
        """Test retrofit time validation with valid positive values."""
        valid_times = [1, 15, 30, 60, 120, 999]

        for retrofit_time in valid_times:
            track = Track(id='TRACK01', capacity=5, retrofit_time_min=retrofit_time)
            assert track.retrofit_time_min == retrofit_time

    def test_track_retrofit_time_validation_invalid_values(self):
        """Test retrofit time validation with invalid values."""
        invalid_times = [0, -1, -30]

        for retrofit_time in invalid_times:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=5, retrofit_time_min=retrofit_time)
            assert 'greater than 0' in str(exc_info.value)

    def test_track_retrofit_time_validation_non_integer(self):
        """Test retrofit time validation with non-integer values."""
        # Pydantic converts some values successfully, so we split into convertible and non-convertible

        # Test values that Pydantic can convert to integers
        convertible_values = [
            ('30', 30),  # string to int
            (30.0, 30),  # float without fractional part
        ]

        for input_val, expected_val in convertible_values:
            track = Track(id='TRACK01', capacity=5, retrofit_time_min=input_val)
            assert track.retrofit_time_min == expected_val
            assert isinstance(track.retrofit_time_min, int)

        # Test values that should raise ValidationError (floats with fractional parts)
        invalid_fractional = [30.5, 45.7]
        for retrofit_time in invalid_fractional:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=5, retrofit_time_min=retrofit_time)
            error_msg = str(exc_info.value)
            assert 'got a number with a fractional part' in error_msg

        # Test values that cannot be converted at all
        non_convertible = [None, [], {}, 'abc']
        for retrofit_time in non_convertible:
            with pytest.raises(ValidationError) as exc_info:
                Track(id='TRACK01', capacity=5, retrofit_time_min=retrofit_time)
            error_msg = str(exc_info.value)
            assert (
                'Input should be a valid integer' in error_msg
                or 'greater than 0' in error_msg
                or 'Field required' in error_msg
            )

    def test_track_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        # Missing id
        with pytest.raises(ValidationError) as exc_info:
            Track(capacity=5, retrofit_time_min=30)
        assert 'Field required' in str(exc_info.value)

        # Missing capacity
        with pytest.raises(ValidationError) as exc_info:
            Track(id='TRACK01', retrofit_time_min=30)
        assert 'Field required' in str(exc_info.value)

        # Missing retrofit_time_min
        with pytest.raises(ValidationError) as exc_info:
            Track(id='TRACK01', capacity=5)
        assert 'Field required' in str(exc_info.value)

    def test_track_equality(self):
        """Test track equality comparison."""
        track1 = Track(id='TRACK01', capacity=5, retrofit_time_min=30)
        track2 = Track(id='TRACK01', capacity=5, retrofit_time_min=30)
        track3 = Track(id='TRACK02', capacity=5, retrofit_time_min=30)

        assert track1 == track2
        assert track1 != track3

    def test_track_dict_conversion(self):
        """Test track conversion to dictionary."""
        track = Track(id='TRACK01', capacity=5, retrofit_time_min=30)
        track_dict = track.model_dump()

        expected_dict = {'id': 'TRACK01', 'capacity': 5, 'retrofit_time_min': 30}

        assert track_dict == expected_dict

    def test_track_json_serialization(self):
        """Test track JSON serialization."""
        track = Track(id='TRACK01', capacity=5, retrofit_time_min=30)
        json_str = track.model_dump_json()

        # Should be valid JSON that can be parsed back
        import json

        parsed = json.loads(json_str)

        assert parsed['id'] == 'TRACK01'
        assert parsed['capacity'] == 5
        assert parsed['retrofit_time_min'] == 30

    def test_track_from_dict(self):
        """Test track creation from dictionary."""
        track_data = {'id': 'TRACK01', 'capacity': 5, 'retrofit_time_min': 30}

        track = Track(**track_data)

        assert track.id == 'TRACK01'
        assert track.capacity == 5
        assert track.retrofit_time_min == 30
