"""
Unit tests for WorkshopTrack model.

Tests the WorkshopTrack model validation logic, field constraints,
and error handling for workshop track configurations.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from configuration.model_track import TrackFunction, WorkshopTrack


class TestWorkshopTrack:
    """Test cases for WorkshopTrack model."""

    def test_track_creation_valid_data(self) -> None:
        """Test successful track creation with valid data."""
        track = WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)

        assert track.id == 'TRACK01'
        assert track.function == TrackFunction.WERKSTATTGLEIS
        assert track.capacity == 5
        assert track.current_wagons == []  # Default is now empty list
        assert track.retrofit_time_min == 30

    def test_track_id_validation_valid_formats(self):
        """Test track ID validation with valid formats (TRACK01-TRACK99)."""
        valid_ids = [
            'TRACK01',
            'TRACK02',
            'TRACK10',
            'TRACK99',
        ]

        for track_id in valid_ids:
            track = WorkshopTrack(id=track_id, function=TrackFunction.WERKSTATTGLEIS, capacity=1, retrofit_time_min=1)
            assert track.id == track_id

    def test_track_id_validation_invalid_formats(self):
        """Test track ID validation with invalid formats."""
        invalid_ids = [
            '',  # Empty string
            'TRACK1',  # Only one digit
            'TRACK001',  # Three digits
            'TRACKA1',  # Letter in number
            'TRACK 01',  # Space in middle
            'TRACK@01',  # Special character
            'TRACK.01',  # Dot
            'TRACK#01',  # Hash
            'TRACK/01',  # Slash
            'TRACK+01',  # Plus
            'track01',  # Lowercase
            'TRACK100',  # Out of range
            'TRACK',  # Too short
            'TRACK1A',  # Letter in number
            'TRACK-01',  # Hyphen
            'TRACK_01',  # Underscore
            'T' * 21,  # Too long
        ]

        for track_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(id=track_id, function=TrackFunction.WERKSTATTGLEIS, capacity=1, retrofit_time_min=1)
            assert (
                'String should match pattern' in str(exc_info.value)
                or 'at least 7 characters' in str(exc_info.value)
                or 'at most 7 characters' in str(exc_info.value)
            )

    def test_track_function_validation(self):
        """Test function field validation with all enum values."""
        for function in TrackFunction:
            retrofit_time = 30 if function == TrackFunction.WERKSTATTGLEIS else 0
            track = WorkshopTrack(id='TRACK01', function=function, capacity=5, retrofit_time_min=retrofit_time)
            assert track.function == function

    def test_track_capacity_validation_valid_values(self):
        """Test capacity validation with valid positive values."""
        valid_capacities = [1, 5, 10, 100, 999]

        for capacity in valid_capacities:
            track = WorkshopTrack(
                id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=capacity, retrofit_time_min=30
            )
            assert track.capacity == capacity

    def test_track_capacity_validation_invalid_values(self):
        """Test capacity validation with invalid values."""
        invalid_capacities = [0, -1, -10]

        for capacity in invalid_capacities:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=capacity, retrofit_time_min=30
                )
            assert 'greater than 0' in str(exc_info.value)

    def test_track_capacity_validation_non_integer(self):
        """Test capacity validation with non-integer values."""
        # Test values that Pydantic can convert to integers
        convertible_values = [
            ('5', 5),  # string to int
            (1.0, 1),  # float without fractional part
        ]

        for input_val, expected_val in convertible_values:
            track = WorkshopTrack(
                id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=input_val, retrofit_time_min=30
            )
            assert track.capacity == expected_val
            assert isinstance(track.capacity, int)

        # Test values that should raise ValidationError (floats with fractional parts)
        invalid_fractional = [1.5, 2.7]
        for capacity in invalid_fractional:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=capacity, retrofit_time_min=30
                )
            error_msg = str(exc_info.value)
            assert 'got a number with a fractional part' in error_msg

        # Test values that cannot be converted at all
        non_convertible = [None, [], {}, 'abc']
        for capacity in non_convertible:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=capacity, retrofit_time_min=30
                )
            error_msg = str(exc_info.value)
            assert (
                'Input should be a valid integer' in error_msg
                or 'greater than 0' in error_msg
                or 'Field required' in error_msg
            )

    def test_track_retrofit_time_validation_werkstattgleis(self):
        """Test retrofit time validation for werkstattgleis (must be > 0)."""
        valid_times = [1, 15, 30, 60, 120, 999]

        for retrofit_time in valid_times:
            track = WorkshopTrack(
                id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=retrofit_time
            )
            assert track.retrofit_time_min == retrofit_time

        # Test invalid values for werkstattgleis (should be > 0)
        invalid_times = [0, -1, -30]
        for retrofit_time in invalid_times:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=retrofit_time
                )
            # Should fail either at field level (ge=0) or model level validation
            error_msg = str(exc_info.value)
            assert 'greater than or equal to 0' in error_msg or 'must be > 0 for werkstattgleis' in error_msg

    def test_track_retrofit_time_validation_non_werkstattgleis(self):
        """Test retrofit time validation for non-werkstattgleis functions (must be 0)."""
        non_werkstatt_functions = [f for f in TrackFunction if f != TrackFunction.WERKSTATTGLEIS]

        for function in non_werkstatt_functions:
            # Valid case: retrofit_time_min = 0
            track = WorkshopTrack(id='TRACK01', function=function, capacity=5, retrofit_time_min=0)
            assert track.retrofit_time_min == 0

            # Invalid case: retrofit_time_min != 0
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(id='TRACK01', function=function, capacity=5, retrofit_time_min=30)
            assert 'must be 0 unless function is werkstattgleis' in str(exc_info.value)

    def test_track_function_sammelgleis(self):
        """Test SAMMELGLEIS function validation."""
        # Valid case: retrofit_time_min = 0
        track = WorkshopTrack(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=0)
        assert track.function == TrackFunction.SAMMELGLEIS
        assert track.retrofit_time_min == 0
        assert track.capacity == 10

        # Invalid case: retrofit_time_min != 0
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrack(id='TRACK03', function=TrackFunction.SAMMELGLEIS, capacity=10, retrofit_time_min=15)
        assert 'must be 0 unless function is werkstattgleis' in str(exc_info.value)

    def test_track_function_parkgleis(self):
        """Test PARKGLEIS function validation."""
        # Valid case: retrofit_time_min = 0
        track = WorkshopTrack(id='TRACK04', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=0)
        assert track.function == TrackFunction.PARKGLEIS
        assert track.retrofit_time_min == 0
        assert track.capacity == 8

        # Invalid case: retrofit_time_min != 0
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrack(id='TRACK04', function=TrackFunction.PARKGLEIS, capacity=8, retrofit_time_min=20)
        assert 'must be 0 unless function is werkstattgleis' in str(exc_info.value)

    def test_track_function_werkstattgleis(self):
        """Test WERKSTATTGLEIS function validation."""
        # Valid case: retrofit_time_min > 0
        track = WorkshopTrack(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=6, retrofit_time_min=45)
        assert track.function == TrackFunction.WERKSTATTGLEIS
        assert track.retrofit_time_min == 45
        assert track.capacity == 6

        # Invalid case: retrofit_time_min = 0
        with pytest.raises(ValidationError) as exc_info:
            WorkshopTrack(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=6, retrofit_time_min=0)
        assert 'must be > 0 for werkstattgleis' in str(exc_info.value)

    def test_current_wagons_field_defaults_to_empty_list(self) -> None:
        """Test that current_wagons field defaults to empty list when not provided."""
        track = WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)
        assert track.current_wagons == []  # Default is now empty list

    def test_current_wagons_field_valid_values(self) -> None:
        """Test current_wagons validation with valid list values."""
        valid_values = [
            [],  # Empty list
            [1],  # Single wagon ID
            [1, 2, 3],  # Multiple wagon IDs
            [100, 200, 300, 400, 500],  # Many wagon IDs
        ]

        for current_wagons in valid_values:
            track = WorkshopTrack(
                id='TRACK01',
                function=TrackFunction.WERKSTATTGLEIS,
                capacity=10,
                current_wagons=current_wagons,
                retrofit_time_min=30,
            )
            assert track.current_wagons == current_wagons

    def test_current_wagons_field_invalid_values(self) -> None:
        """Test current_wagons validation with invalid list values."""
        invalid_values = [
            [1, -1, 3],  # List with negative wagon ID
            [-5],  # Single negative wagon ID
            [1, 2, -10, 4],  # Mixed positive and negative wagon IDs
            ['abc'],  # List with non-integer strings
            [1.5, 2.7],  # List with floats
            [None],  # List with None value
        ]

        for current_wagons in invalid_values:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01',
                    function=TrackFunction.WERKSTATTGLEIS,
                    capacity=10,
                    current_wagons=current_wagons,
                    retrofit_time_min=30,
                )
            error_msg = str(exc_info.value)
            # Should contain validation error for list contents
            assert any(
                phrase in error_msg
                for phrase in ['greater than or equal to 0', 'Input should be a valid integer', 'Field required']
            )

    def test_current_wagons_field_invalid_non_list_values(self) -> None:
        """Test current_wagons validation with non-list values."""
        invalid_non_list_values = [
            None,  # None not allowed anymore
            'string',  # String
            123,  # Integer
            12.34,  # Float
            {'key': 'value'},  # Dict
        ]

        for current_wagons in invalid_non_list_values:
            with pytest.raises(ValidationError) as exc_info:
                WorkshopTrack(
                    id='TRACK01',
                    function=TrackFunction.WERKSTATTGLEIS,
                    capacity=10,
                    current_wagons=current_wagons,
                    retrofit_time_min=30,
                )
            error_msg = str(exc_info.value)
            # Should contain validation error about expecting a list
            assert any(
                phrase in error_msg for phrase in ['Input should be a valid list', 'list required', 'Field required']
            )

    def test_is_available_method_with_none_current_wagons(self):
        """Test is_available method when current_wagons is None."""
        track = WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)
        assert track.current_wagons == []  # Default is now empty list
        assert track.is_available() is True

    def test_is_available_method_with_empty_current_wagons(self) -> None:
        """Test is_available method when current_wagons is empty list."""
        track = WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)
        assert track.current_wagons == []  # Default is now empty list
        assert track.is_available() is True

    def test_is_available_method_with_current_wagons_less_than_capacity(self) -> None:
        """Test is_available method when current_wagons list length < capacity."""
        track = WorkshopTrack(
            id='TRACK01',
            function=TrackFunction.WERKSTATTGLEIS,
            capacity=5,
            current_wagons=[1, 2, 3],
            retrofit_time_min=30,
        )
        assert len(track.current_wagons) == 3
        assert track.capacity == 5
        assert track.is_available() is True

    def test_is_available_method_with_current_wagons_equal_to_capacity(self) -> None:
        """Test is_available method when current_wagons list length equals capacity."""
        track = WorkshopTrack(
            id='TRACK01',
            function=TrackFunction.WERKSTATTGLEIS,
            capacity=5,
            current_wagons=[1, 2, 3, 4, 5],
            retrofit_time_min=30,
        )
        assert len(track.current_wagons) == 5
        assert track.capacity == 5
        assert track.is_available() is False

    def test_is_available_method_with_current_wagons_greater_than_capacity(self) -> None:
        """Test is_available method when current_wagons list length > capacity."""
        # Note: This scenario might occur in edge cases or data inconsistencies
        track = WorkshopTrack(
            id='TRACK01',
            function=TrackFunction.WERKSTATTGLEIS,
            capacity=5,
            current_wagons=[1, 2, 3, 4, 5, 6, 7],
            retrofit_time_min=30,
        )
        assert len(track.current_wagons) == 7
        assert track.capacity == 5
        assert track.is_available() is False

    def test_track_creation_with_all_fields(self) -> None:
        """Test track creation with all fields including current_wagons."""
        track = WorkshopTrack(
            id='TRACK05', function=TrackFunction.SAMMELGLEIS, capacity=8, current_wagons=[101, 102], retrofit_time_min=0
        )

        assert track.id == 'TRACK05'
        assert track.function == TrackFunction.SAMMELGLEIS
        assert track.capacity == 8
        assert track.current_wagons == [101, 102]
        assert track.retrofit_time_min == 0
        assert track.is_available() is True

    def test_csv_data_format_validation(self):
        """Test validation using the exact CSV data format you provided."""
        # Test cases from your CSV data
        csv_test_cases = [
            ('TRACK01', 'werkstattgleis', 5, 30),
            ('TRACK02', 'werkstattgleis', 3, 45),
            ('TRACK03', 'sammelgleis', 10, 0),
            ('TRACK04', 'parkgleis', 8, 0),
            ('TRACK05', 'werkstattzufuehrung', 2, 0),
            ('TRACK06', 'werkstattabfuehrung', 2, 0),
            ('TRACK07', 'bahnhofskopf', 3, 0),
        ]

        for track_id, function_str, capacity, retrofit_time in csv_test_cases:
            # Test creation from dictionary (simulates pandas.to_dict('records'))
            track_data = {
                'id': track_id,
                'function': function_str,
                'capacity': capacity,
                'retrofit_time_min': retrofit_time,
            }

            track = WorkshopTrack(**track_data)

            assert track.id == track_id
            assert track.function.value == function_str  # Enum value matches string
            assert track.capacity == capacity
            assert track.retrofit_time_min == retrofit_time

    def test_pandas_csv_integration(self):
        """Test integration with pandas CSV loading workflow."""
        # Load test data from CSV file
        csv_file_path = Path(__file__).parent.parent / 'fixtures' / 'config' / 'test_workshop_tracks.csv'

        # Read CSV file
        with open(csv_file_path, 'r') as f:
            csv_content = f.read()

        # Parse CSV manually (simulating pandas behavior)
        lines = csv_content.strip().split('\n')
        headers = lines[0].split(',')

        tracks = []
        for line in lines[1:]:
            values = line.split(',')
            row_dict = {headers[i]: values[i] for i in range(len(headers))}

            # Convert types (pandas would do this automatically)
            track_data = {
                'id': row_dict['track_id'],  # Rename to match model
                'function': row_dict['function'],
                'capacity': int(row_dict['capacity']),
                'retrofit_time_min': int(row_dict['retrofit_time_min']),
            }

            # Create track instance
            track = WorkshopTrack(**track_data)
            tracks.append(track)

        # Verify all tracks were created successfully
        assert len(tracks) == 7

        # Verify specific tracks
        assert tracks[0].id == 'TRACK01'
        assert tracks[0].function == TrackFunction.WERKSTATTGLEIS
        assert tracks[2].function == TrackFunction.SAMMELGLEIS
        assert tracks[6].function == TrackFunction.BAHNHOFSKOPF
