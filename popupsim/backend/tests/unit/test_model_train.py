"""
Unit tests for TrainArrival model.

Tests the TrainArrival model validation logic, time parsing,
wagon validation, and datetime combination functionality.
"""

from datetime import date, datetime, time, timezone

import pytest
from pydantic import ValidationError

from src.configuration.model_train import TrainArrival
from src.configuration.model_wagon import WagonInfo


class TestTrainArrival:
    """Test cases for TrainArrival model."""

    def test_train_arrival_creation_valid_data(self):
        """Test successful train arrival creation with valid data."""
        wagons = [
            WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False),
            WagonInfo(wagon_id='W002', length=12.0, is_loaded=False, needs_retrofit=True),
        ]

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        assert train.train_id == 'TRAIN001'
        assert train.arrival_date == date(2024, 1, 15)
        assert train.arrival_time == time(8, 30)
        assert len(train.wagons) == 2
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_datetime_property(self):
        """Test the arrival_datetime property combines date and time correctly."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(14, 30, 45), wagons=wagons
        )

        expected_datetime = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        assert train.arrival_datetime == expected_datetime

    def test_train_arrival_time_string_parsing_valid_formats(self):
        """Test parsing of arrival time from valid string formats."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        valid_time_strings = [
            ('08:30', time(8, 30)),
            ('14:45', time(14, 45)),
            ('00:00', time(0, 0)),
            ('23:59', time(23, 59)),
            ('09:07', time(9, 7)),
            ('18:22', time(18, 22)),
        ]

        for time_str, expected_time in valid_time_strings:
            train = TrainArrival(
                train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time_str, wagons=wagons
            )
            assert train.arrival_time == expected_time

    def test_train_arrival_time_string_parsing_invalid_formats(self):
        """Test validation error with invalid time string formats."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        invalid_time_strings = [
            '25:30',  # Invalid hour
            '14:60',  # Invalid minute
            '8:30',  # Missing leading zero
            '08:5',  # Missing leading zero for minute
            '24:00',  # Hour 24 is invalid
            '14:30:00',  # Seconds not allowed in this format
            '14.30',  # Wrong separator
            '14-30',  # Wrong separator
            'abc',  # Non-numeric
            '',  # Empty string
            '14',  # Missing minute
            ':30',  # Missing hour
            '14:',  # Missing minute
        ]

        for time_str in invalid_time_strings:
            with pytest.raises(ValidationError) as exc_info:
                TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time_str, wagons=wagons)
            assert 'arrival_time must be in HH:MM format' in str(exc_info.value)

    def test_train_arrival_time_object_validation(self):
        """Test that time objects are accepted directly."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        time_obj = time(14, 30, 45)
        train = TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time_obj, wagons=wagons)

        assert train.arrival_time == time_obj

    def test_train_arrival_time_invalid_types(self):
        """Test validation error with invalid time types."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        invalid_time_values = [
            123,  # Integer
            14.30,  # Float
            [],  # List
            {},  # Dict
            datetime.now(tz=timezone.utc),  # DateTime object
        ]

        for time_val in invalid_time_values:
            with pytest.raises(ValidationError) as exc_info:
                TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time_val, wagons=wagons)
            error_msg = str(exc_info.value)
            assert (
                'arrival_time must be a string in HH:MM format or a time object' in error_msg
                or 'arrival_time must be in HH:MM format' in error_msg
            )

    def test_train_arrival_empty_wagons_validation(self):
        """Test validation error when wagons list is empty."""
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=[])
        assert 'must have at least one wagon' in str(exc_info.value)

    def test_train_arrival_missing_wagons_field(self):
        """Test validation error when wagons field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30))
        assert 'Field required' in str(exc_info.value)

    def test_train_arrival_single_wagon(self):
        """Test train arrival with single wagon."""
        wagon = WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=[wagon]
        )

        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_multiple_wagons(self):
        """Test train arrival with multiple wagons."""
        wagons = [
            WagonInfo(wagon_id=f'W{i:03d}', length=15.5, is_loaded=i % 2 == 0, needs_retrofit=i % 3 == 0)
            for i in range(1, 11)  # 10 wagons
        ]

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        assert len(train.wagons) == 10
        assert train.wagons[0].wagon_id == 'W001'
        assert train.wagons[9].wagon_id == 'W010'

    def test_train_arrival_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        # Missing train_id
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons)
        assert 'Field required' in str(exc_info.value)

        # Missing arrival_date
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(train_id='TRAIN001', arrival_time=time(8, 30), wagons=wagons)
        assert 'Field required' in str(exc_info.value)

        # Missing arrival_time
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(train_id='TRAIN001', arrival_date=date(2024, 1, 15), wagons=wagons)
        # arrival_time field shows a different error message when missing
        error_msg = str(exc_info.value)
        assert 'Field required' in error_msg or 'Input should be a valid time' in error_msg

    def test_train_arrival_date_validation(self):
        """Test arrival_date field validation."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        # Valid date formats
        valid_dates = [
            date(2024, 1, 1),
            date(2024, 12, 31),
            date(2000, 2, 29),  # Leap year
            '2024-01-15',  # String format should be converted
        ]

        for test_date in valid_dates:
            train = TrainArrival(train_id='TRAIN001', arrival_date=test_date, arrival_time=time(8, 30), wagons=wagons)
            if isinstance(test_date, str):
                assert train.arrival_date == date(2024, 1, 15)
            else:
                assert train.arrival_date == test_date

    def test_train_arrival_equality(self):
        """Test train arrival equality comparison."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        train1 = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        train2 = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        train3 = TrainArrival(
            train_id='TRAIN002', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        assert train1 == train2
        assert train1 != train3

    def test_train_arrival_dict_conversion(self):
        """Test train arrival conversion to dictionary."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        train_dict = train.model_dump()

        assert train_dict['train_id'] == 'TRAIN001'
        assert train_dict['arrival_date'] == date(2024, 1, 15)
        assert train_dict['arrival_time'] == time(8, 30)
        assert len(train_dict['wagons']) == 1
        assert train_dict['wagons'][0]['wagon_id'] == 'W001'

    def test_train_arrival_json_serialization(self):
        """Test train arrival JSON serialization."""
        wagons = [WagonInfo(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False)]

        train = TrainArrival(
            train_id='TRAIN001', arrival_date=date(2024, 1, 15), arrival_time=time(8, 30), wagons=wagons
        )

        json_str = train.model_dump_json()

        # Should be valid JSON that can be parsed back
        import json

        parsed = json.loads(json_str)

        assert parsed['train_id'] == 'TRAIN001'
        assert parsed['arrival_date'] == '2024-01-15'
        assert parsed['arrival_time'] == '08:30:00'
        assert len(parsed['wagons']) == 1

    def test_train_arrival_from_dict(self):
        """Test train arrival creation from dictionary."""
        train_data = {
            'train_id': 'TRAIN001',
            'arrival_date': '2024-01-15',
            'arrival_time': '08:30',
            'wagons': [{'wagon_id': 'W001', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}],
        }

        train = TrainArrival(**train_data)

        assert train.train_id == 'TRAIN001'
        assert train.arrival_date == date(2024, 1, 15)
        assert train.arrival_time == time(8, 30)
        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_realistic_scenarios(self):
        """Test train arrival with realistic scenario data."""
        # Early morning freight train
        freight_wagons = [
            WagonInfo(wagon_id='FREIGHT_001', length=20.0, is_loaded=True, needs_retrofit=False),
            WagonInfo(wagon_id='FREIGHT_002', length=20.0, is_loaded=True, needs_retrofit=True),
            WagonInfo(wagon_id='FREIGHT_003', length=18.5, is_loaded=False, needs_retrofit=False),
        ]

        freight_train = TrainArrival(
            train_id='FREIGHT_001', arrival_date=date(2024, 1, 15), arrival_time='06:15', wagons=freight_wagons
        )

        assert freight_train.train_id == 'FREIGHT_001'
        assert freight_train.arrival_time == time(6, 15)
        assert len(freight_train.wagons) == 3

        # Late night maintenance train
        maint_wagons = [WagonInfo(wagon_id='MAINT_001', length=12.0, is_loaded=False, needs_retrofit=True)]

        maint_train = TrainArrival(
            train_id='MAINT_SPECIAL', arrival_date=date(2024, 1, 16), arrival_time=time(23, 45), wagons=maint_wagons
        )

        assert maint_train.train_id == 'MAINT_SPECIAL'
        assert maint_train.arrival_datetime == datetime(2024, 1, 16, 23, 45, tzinfo=timezone.utc)
        assert maint_train.wagons[0].needs_retrofit is True
