"""
Tests for the Wagon model.

This module contains unit tests for the Wagon model, including validation,
property calculations, and edge case handling.
"""

from typing import Any

from models.wagon import Wagon
from pydantic import ValidationError
import pytest


class TestWagon:
    """Test cases for the Wagon model."""

    def test_wagon_creation_with_minimal_data(self) -> None:
        """Test creating a wagon with minimal required data."""
        wagon = Wagon(wagon_id='W001', train_id='T001', length=15.5, is_loaded=True, needs_retrofit=False)

        assert wagon.wagon_id == 'W001'
        assert wagon.train_id == 'T001'
        assert wagon.length == 15.5
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False
        assert wagon.arrival_time is None
        assert wagon.retrofit_start_time is None
        assert wagon.retrofit_end_time is None
        assert wagon.track_id is None

    def test_wagon_creation_with_all_data(self) -> None:
        """Test creating a wagon with all fields populated."""
        wagon = Wagon(
            wagon_id='W002',
            train_id='T002',
            length=20.0,
            is_loaded=False,
            needs_retrofit=True,
            arrival_time=100.0,
            retrofit_start_time=150.0,
            retrofit_end_time=200.0,
            track_id='TRACK_001',
        )

        assert wagon.wagon_id == 'W002'
        assert wagon.train_id == 'T002'
        assert wagon.length == 20.0
        assert wagon.is_loaded is False
        assert wagon.needs_retrofit is True
        assert wagon.arrival_time == 100.0
        assert wagon.retrofit_start_time == 150.0
        assert wagon.retrofit_end_time == 200.0
        assert wagon.track_id == 'TRACK_001'

    def test_wagon_length_validation_positive(self) -> None:
        """Test that wagon length must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Wagon(
                wagon_id='W003',
                train_id='T003',
                length=0,  # Invalid: must be > 0
                is_loaded=True,
                needs_retrofit=False,
            )

        error = exc_info.value.errors()[0]
        assert error['type'] == 'greater_than'
        assert 'length' in error['loc']

    def test_wagon_length_validation_negative(self) -> None:
        """Test that negative wagon length is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            Wagon(
                wagon_id='W004',
                train_id='T004',
                length=-5.0,  # Invalid: must be > 0
                is_loaded=True,
                needs_retrofit=False,
            )

        error = exc_info.value.errors()[0]
        assert error['type'] == 'greater_than'
        assert 'length' in error['loc']

    def test_wagon_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Wagon(
                wagon_id='W005',
                # Missing train_id, length, is_loaded, needs_retrofit
            )

        errors = exc_info.value.errors()
        missing_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        expected_missing = {'train_id', 'length', 'is_loaded', 'needs_retrofit'}
        assert expected_missing.issubset(missing_fields)

    def test_wagon_waiting_time_calculation(self) -> None:
        """Test waiting time calculation when both times are available."""
        wagon = Wagon(
            wagon_id='W006',
            train_id='T006',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            arrival_time=100.0,
            retrofit_start_time=180.0,
        )

        assert wagon.waiting_time == 80.0

    def test_wagon_waiting_time_no_arrival(self) -> None:
        """Test waiting time is None when arrival_time is not set."""
        wagon = Wagon(
            wagon_id='W007',
            train_id='T007',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            retrofit_start_time=180.0,
            # arrival_time is None
        )

        assert wagon.waiting_time is None

    def test_wagon_waiting_time_no_retrofit_start(self) -> None:
        """Test waiting time is None when retrofit_start_time is not set."""
        wagon = Wagon(
            wagon_id='W008',
            train_id='T008',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            arrival_time=100.0,
            # retrofit_start_time is None
        )

        assert wagon.waiting_time is None

    def test_wagon_waiting_time_both_none(self) -> None:
        """Test waiting time is None when both times are not set."""
        wagon = Wagon(
            wagon_id='W009',
            train_id='T009',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            # Both arrival_time and retrofit_start_time are None
        )

        assert wagon.waiting_time is None

    def test_wagon_waiting_time_zero(self) -> None:
        """Test waiting time calculation when times are equal."""
        wagon = Wagon(
            wagon_id='W010',
            train_id='T010',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            arrival_time=150.0,
            retrofit_start_time=150.0,
        )

        assert wagon.waiting_time == 0.0

    def test_wagon_waiting_time_negative(self) -> None:
        """Test waiting time can be negative if retrofit starts before arrival."""
        wagon = Wagon(
            wagon_id='W011',
            train_id='T011',
            length=12.0,
            is_loaded=True,
            needs_retrofit=True,
            arrival_time=200.0,
            retrofit_start_time=150.0,  # Earlier than arrival
        )

        assert wagon.waiting_time == -50.0

    @pytest.mark.parametrize('length_value', [0.1, 1.0, 10.5, 25.0, 100.0])
    def test_wagon_valid_lengths(self, length_value: float) -> None:
        """Test various valid length values."""
        wagon = Wagon(wagon_id='W_PARAM', train_id='T_PARAM', length=length_value, is_loaded=True, needs_retrofit=False)

        assert wagon.length == length_value

    @pytest.mark.parametrize(
        ('is_loaded', 'needs_retrofit'), [(True, True), (True, False), (False, True), (False, False)]
    )
    def test_wagon_boolean_combinations(self, is_loaded: bool, needs_retrofit: bool) -> None:
        """Test all combinations of boolean fields."""
        wagon = Wagon(
            wagon_id='W_BOOL',
            train_id='T_BOOL',
            length=15.0,
            is_loaded=is_loaded,
            needs_retrofit=needs_retrofit,
        )

        assert wagon.is_loaded == is_loaded
        assert wagon.needs_retrofit == needs_retrofit

    def test_wagon_string_field_types(self) -> None:
        """Test that string fields accept various string values."""
        test_cases = [
            ('', ''),  # Empty strings
            ('W001', 'T001'),  # Simple IDs
            ('WAGON_001_SPECIAL', 'TRAIN_001_SPECIAL'),  # Complex IDs
            ('123', '456'),  # Numeric strings
            ('W-001', 'T-001'),  # IDs with special characters
        ]

        for wagon_id, train_id in test_cases:
            wagon = Wagon(wagon_id=wagon_id, train_id=train_id, length=10.0, is_loaded=True, needs_retrofit=False)

            assert wagon.wagon_id == wagon_id
            assert wagon.train_id == train_id

    def test_wagon_optional_track_id(self) -> None:
        """Test track_id optional field behavior."""
        # Test with None (default)
        wagon1 = Wagon(wagon_id='W012', train_id='T012', length=10.0, is_loaded=True, needs_retrofit=False)
        assert wagon1.track_id is None

        # Test with explicit value
        wagon2 = Wagon(
            wagon_id='W013', train_id='T013', length=10.0, is_loaded=True, needs_retrofit=False, track_id='TRACK_A'
        )
        assert wagon2.track_id == 'TRACK_A'

    def test_wagon_model_dict_representation(self) -> None:
        """Test that wagon can be converted to dictionary."""
        wagon = Wagon(
            wagon_id='W014',
            train_id='T014',
            length=18.5,
            is_loaded=False,
            needs_retrofit=True,
            arrival_time=120.0,
            retrofit_start_time=180.0,
            retrofit_end_time=240.0,
            track_id='TRACK_B',
        )

        wagon_dict = wagon.model_dump()

        expected_dict = {
            'wagon_id': 'W014',
            'train_id': 'T014',
            'length': 18.5,
            'is_loaded': False,
            'needs_retrofit': True,
            'arrival_time': 120.0,
            'retrofit_start_time': 180.0,
            'retrofit_end_time': 240.0,
            'track_id': 'TRACK_B',
        }

        assert wagon_dict == expected_dict

    def test_wagon_from_dict(self) -> None:
        """Test creating wagon from dictionary data."""
        wagon_data: dict[str, Any] = {
            'wagon_id': 'W015',
            'train_id': 'T015',
            'length': 22.0,
            'is_loaded': True,
            'needs_retrofit': False,
            'arrival_time': 90.0,
            'retrofit_start_time': None,
            'retrofit_end_time': None,
            'track_id': 'TRACK_C',
        }

        wagon = Wagon(**wagon_data)

        assert wagon.wagon_id == 'W015'
        assert wagon.train_id == 'T015'
        assert wagon.length == 22.0
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False
        assert wagon.arrival_time == 90.0
        assert wagon.retrofit_start_time is None
        assert wagon.retrofit_end_time is None
        assert wagon.track_id == 'TRACK_C'
