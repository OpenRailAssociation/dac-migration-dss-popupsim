"""
Tests for the Wagon model.

This module contains unit tests for the Wagon model, including validation,
property calculations, and edge case handling.
"""

from datetime import UTC
from datetime import datetime
from typing import Any

from pydantic import ValidationError
import pytest
from workshop_operations.domain.entities.wagon import Wagon


class TestWagon:
    """Test cases for the Wagon model."""

    def test_wagon_creation_with_minimal_data(self) -> None:
        """Test creating a wagon with minimal required data."""
        wagon = Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)

        assert wagon.wagon_id == 'W001'
        assert wagon.length == 15.5
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False
        assert wagon.arrival_time is None
        assert wagon.retrofit_start_time is None

    def test_wagon_creation_with_all_data(self) -> None:
        """Test creating a wagon with all fields populated."""
        wagon = Wagon(
            wagon_id='W002',
            length=20.0,
            is_loaded=False,
            needs_retrofit=True,
            arrival_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            retrofit_start_time=150.0,
            retrofit_end_time=200.0,
        )

        assert wagon.wagon_id == 'W002'
        assert wagon.length == 20.0
        assert wagon.is_loaded is False
        assert wagon.needs_retrofit is True
        assert wagon.arrival_time == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert wagon.retrofit_start_time == 150.0
        assert wagon.retrofit_end_time == 200.0

    def test_wagon_length_validation_positive(self) -> None:
        """Test that wagon length must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Wagon(
                wagon_id='W003',
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
                # Missing length, is_loaded, needs_retrofit
            )

        errors = exc_info.value.errors()
        missing_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        expected_missing = {'length', 'is_loaded', 'needs_retrofit'}
        assert expected_missing.issubset(missing_fields)

    def test_wagon_waiting_time_calculation(self) -> None:
        """Test waiting time calculation when both times are available."""
        wagon = Wagon(
            wagon_id='W006',
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
        wagon = Wagon(wagon_id='W_PARAM', length=length_value, is_loaded=True, needs_retrofit=False)

        assert wagon.length == length_value

    @pytest.mark.parametrize(
        ('is_loaded', 'needs_retrofit'), [(True, True), (True, False), (False, True), (False, False)]
    )
    def test_wagon_boolean_combinations(self, is_loaded: bool, needs_retrofit: bool) -> None:
        """Test all combinations of boolean fields."""
        wagon = Wagon(
            wagon_id='W_BOOL',
            length=15.0,
            is_loaded=is_loaded,
            needs_retrofit=needs_retrofit,
        )

        assert wagon.is_loaded == is_loaded
        assert wagon.needs_retrofit == needs_retrofit

    def test_wagon_model_dict_representation(self) -> None:
        """Test that wagon can be converted to dictionary."""
        wagon = Wagon(
            wagon_id='W014',
            length=18.5,
            is_loaded=False,
            needs_retrofit=True,
            arrival_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            retrofit_start_time=180.0,
            retrofit_end_time=240.0,
        )

        wagon_dict = wagon.model_dump()

        from workshop_operations.domain.entities.wagon import CouplerType
        from workshop_operations.domain.entities.wagon import WagonStatus

        expected_dict = {
            'wagon_id': 'W014',
            'length': 18.5,
            'is_loaded': False,
            'needs_retrofit': True,
            'track_id': None,
            'source_track_id': None,
            'destination_track_id': None,
            'arrival_time': datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            'retrofit_start_time': 180.0,
            'retrofit_end_time': 240.0,
            'status': WagonStatus.UNKNOWN,
            'coupler_type': CouplerType.SCREW,
        }

        assert wagon_dict == expected_dict

    def test_wagon_from_dict(self) -> None:
        """Test creating wagon from dictionary data."""
        wagon_data: dict[str, Any] = {
            'wagon_id': 'W015',
            'length': 22.0,
            'is_loaded': True,
            'needs_retrofit': False,
            'arrival_time': datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            'retrofit_start_time': None,
            'retrofit_end_time': None,
        }

        wagon = Wagon(**wagon_data)

        assert wagon.wagon_id == 'W015'
        assert wagon.length == 22.0
        assert wagon.is_loaded is True
        assert wagon.needs_retrofit is False
        assert wagon.arrival_time == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert wagon.retrofit_start_time is None
        assert wagon.retrofit_end_time is None
