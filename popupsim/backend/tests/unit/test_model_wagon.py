"""
Unit tests for WagonInfo model.

Tests the WagonInfo model validation logic, field constraints,
and error handling for wagon configurations in train simulations.
"""

import pytest
from pydantic import ValidationError

from src.configuration.model_wagon import WagonInfo


class TestWagonInfo:
    """Test cases for WagonInfo model."""

    def test_wagon_creation_valid_data(self):
        """Test successful wagon creation with valid data."""
        wagon = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True, needs_retrofit=False)

        assert wagon.wagon_id == 'WAGON001'
        assert wagon.length == 15.5
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False

    def test_wagon_creation_various_valid_lengths(self):
        """Test wagon creation with various valid length values."""
        valid_lengths = [0.1, 1.0, 15.5, 20.0, 50.75, 100.0]

        for length in valid_lengths:
            wagon = WagonInfo(wagon_id='WAGON001', length=length, is_loaded=True, needs_retrofit=False)
            assert wagon.length == length

    def test_wagon_length_validation_invalid_values(self):
        """Test length validation with invalid values."""
        invalid_lengths = [0, -1.0, -15.5, -0.1]

        for length in invalid_lengths:
            with pytest.raises(ValidationError) as exc_info:
                WagonInfo(wagon_id='WAGON001', length=length, is_loaded=True, needs_retrofit=False)
            assert 'greater than 0' in str(exc_info.value)

    def test_wagon_length_validation_non_numeric(self):
        """Test length validation with non-numeric values."""
        # Pydantic converts some values successfully, so we split into convertible and non-convertible

        # Test values that Pydantic can convert to floats
        convertible_values = [
            ('15.5', 15.5),  # string to float
            ('20', 20.0),  # string integer to float
            (10, 10.0),  # int to float
        ]

        for input_val, expected_val in convertible_values:
            wagon = WagonInfo(wagon_id='WAGON001', length=input_val, is_loaded=True, needs_retrofit=False)
            assert wagon.length == expected_val
            assert isinstance(wagon.length, float)

        # Test values that cannot be converted at all
        non_convertible = [None, [], {}, 'abc', 'invalid']
        for length in non_convertible:
            with pytest.raises(ValidationError) as exc_info:
                WagonInfo(wagon_id='WAGON001', length=length, is_loaded=True, needs_retrofit=False)
            error_msg = str(exc_info.value)
            assert (
                'Input should be a valid number' in error_msg
                or 'Input should be greater than 0' in error_msg
                or 'Field required' in error_msg
            )

    def test_wagon_boolean_field_validation(self):
        """Test validation of boolean fields with various inputs."""
        # Test all combinations of boolean values
        boolean_combinations = [(True, True), (True, False), (False, True), (False, False)]

        for is_loaded, needs_retrofit in boolean_combinations:
            wagon = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=is_loaded, needs_retrofit=needs_retrofit)
            assert wagon.is_loaded == is_loaded
            assert wagon.needs_retrofit == needs_retrofit

    def test_wagon_boolean_field_string_conversion(self):
        """Test boolean field conversion from string values."""
        # Pydantic should convert string representations to boolean
        wagon1 = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded='true', needs_retrofit='false')
        assert wagon1.is_loaded is True
        assert wagon1.needs_retrofit is False

        wagon2 = WagonInfo(wagon_id='WAGON002', length=20.0, is_loaded='1', needs_retrofit='0')
        assert wagon2.is_loaded is True
        assert wagon2.needs_retrofit is False

    def test_wagon_id_validation_various_formats(self):
        """Test wagon ID with various valid formats."""
        valid_ids = [
            'WAGON001',
            'W1',
            'wagon_123',
            'WAGON-456',
            'W',
            '123',
            'WAGON_A1_B2',
            'w' * 50,  # Long ID
            'MixedCase123',
        ]

        for wagon_id in valid_ids:
            wagon = WagonInfo(wagon_id=wagon_id, length=15.5, is_loaded=True, needs_retrofit=False)
            assert wagon.wagon_id == wagon_id

    def test_wagon_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        # Missing wagon_id
        with pytest.raises(ValidationError) as exc_info:
            WagonInfo(length=15.5, is_loaded=True, needs_retrofit=False)
        assert 'Field required' in str(exc_info.value)

        # Missing length
        with pytest.raises(ValidationError) as exc_info:
            WagonInfo(wagon_id='WAGON001', is_loaded=True, needs_retrofit=False)
        assert 'Field required' in str(exc_info.value)

        # Missing is_loaded
        with pytest.raises(ValidationError) as exc_info:
            WagonInfo(wagon_id='WAGON001', length=15.5, needs_retrofit=False)
        assert 'Field required' in str(exc_info.value)

        # Missing needs_retrofit
        with pytest.raises(ValidationError) as exc_info:
            WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True)
        assert 'Field required' in str(exc_info.value)

    def test_wagon_equality(self):
        """Test wagon equality comparison."""
        wagon1 = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True, needs_retrofit=False)
        wagon2 = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True, needs_retrofit=False)
        wagon3 = WagonInfo(wagon_id='WAGON002', length=15.5, is_loaded=True, needs_retrofit=False)

        assert wagon1 == wagon2
        assert wagon1 != wagon3

    def test_wagon_dict_conversion(self):
        """Test wagon conversion to dictionary."""
        wagon = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True, needs_retrofit=False)
        wagon_dict = wagon.model_dump()

        expected_dict = {'wagon_id': 'WAGON001', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}

        assert wagon_dict == expected_dict

    def test_wagon_json_serialization(self):
        """Test wagon JSON serialization."""
        wagon = WagonInfo(wagon_id='WAGON001', length=15.5, is_loaded=True, needs_retrofit=False)
        json_str = wagon.model_dump_json()

        # Should be valid JSON that can be parsed back
        import json

        parsed = json.loads(json_str)

        assert parsed['wagon_id'] == 'WAGON001'
        assert parsed['length'] == 15.5
        assert parsed['is_loaded'] is True
        assert parsed['needs_retrofit'] is False

    def test_wagon_from_dict(self):
        """Test wagon creation from dictionary."""
        wagon_data = {'wagon_id': 'WAGON001', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}

        wagon = WagonInfo(**wagon_data)

        assert wagon.wagon_id == 'WAGON001'
        assert wagon.length == 15.5
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False

    def test_wagon_edge_case_very_small_length(self):
        """Test wagon with very small but valid length."""
        wagon = WagonInfo(
            wagon_id='WAGON001',
            length=0.001,  # Very small but > 0
            is_loaded=False,
            needs_retrofit=True,
        )
        assert wagon.length == 0.001

    def test_wagon_edge_case_very_large_length(self):
        """Test wagon with very large length."""
        wagon = WagonInfo(
            wagon_id='WAGON001',
            length=999999.99,  # Very large length
            is_loaded=False,
            needs_retrofit=True,
        )
        assert wagon.length == 999999.99

    def test_wagon_realistic_scenarios(self):
        """Test wagon creation with realistic scenario data."""
        # Loaded wagon that needs retrofit
        loaded_retrofit = WagonInfo(wagon_id='CARGO_W001', length=18.5, is_loaded=True, needs_retrofit=True)
        assert loaded_retrofit.is_loaded and loaded_retrofit.needs_retrofit

        # Empty wagon that doesn't need retrofit
        empty_good = WagonInfo(wagon_id='EMPTY_W002', length=12.0, is_loaded=False, needs_retrofit=False)
        assert not empty_good.is_loaded and not empty_good.needs_retrofit

        # Empty wagon that needs retrofit
        empty_retrofit = WagonInfo(wagon_id='MAINT_W003', length=20.5, is_loaded=False, needs_retrofit=True)
        assert not empty_retrofit.is_loaded and empty_retrofit.needs_retrofit
