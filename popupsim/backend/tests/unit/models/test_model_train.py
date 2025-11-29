"""
Unit tests for Train model.

Tests the Train model validation logic, time parsing,
wagon validation, and datetime combination functionality.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
import json

from pydantic import ValidationError
import pytest
from workshop_operations.domain.aggregates.train import Train
from workshop_operations.domain.entities.wagon import Wagon


class TestTrain:
    """Test cases for Train model."""

    def test_train_arrival_creation_valid_data(self) -> None:
        """
        Test successful train arrival creation with valid data.

        Notes
        -----
        Validates that Train instances can be created with valid datetime
        and wagon list, and that all fields are correctly assigned.
        """
        wagons = [
            Wagon(id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1'),
            Wagon(id='W002', length=12.0, is_loaded=False, needs_retrofit=True, train_id='1'),
        ]
        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        assert train.train_id == '1'
        assert train.arrival_time == test_date
        assert len(train.wagons) == 2
        assert train.wagons[0].id == 'W001'

    def test_train_arrival_empty_wagons_validation(self) -> None:
        """
        Test validation error when wagons list is empty.

        Notes
        -----
        Validates that attempting to create a Train with an empty wagons
        list raises ValidationError with appropriate message.
        """
        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        with pytest.raises(ValidationError) as exc_info:
            Train(train_id='1', arrival_time=test_date, wagons=[])
        assert 'must have at least one wagon' in str(exc_info.value)

    def test_train_arrival_missing_wagons_field(self) -> None:
        """
        Test validation error when wagons field is missing.

        Notes
        -----
        Validates that omitting the required wagons field raises
        ValidationError with 'Field required' message.
        """
        test_date = datetime(2024, 1, 15, 8, 30, tzinfo=UTC)
        with pytest.raises(ValidationError) as exc_info:
            Train(train_id='1', arrival_time=test_date)  # type: ignore[call-arg]
        assert 'Field required' in str(exc_info.value)

    def test_train_arrival_single_wagon(self) -> None:
        """
        Test train arrival with single wagon.

        Notes
        -----
        Validates that trains with a single wagon are correctly created
        and the wagon details are accessible.
        """
        wagon = Wagon(id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=[wagon])

        assert len(train.wagons) == 1
        assert train.wagons[0].id == 'W001'

    def test_train_arrival_equality(self) -> None:
        """
        Test train arrival equality comparison.

        Notes
        -----
        Validates that Train instances with identical field values are
        considered equal, while instances with different values are not.
        """
        wagons = [Wagon(id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train1 = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train2 = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train3 = Train(train_id='TRAIN002', arrival_time=test_date + timedelta(days=1), wagons=wagons)

        assert train1 == train2
        assert train1 != train3

    def test_train_arrival_dict_conversion(self) -> None:
        """
        Test train arrival conversion to dictionary.

        Notes
        -----
        Validates that Train instances can be converted to dictionary format
        with all fields correctly represented, including nested wagon data.
        """
        wagons = [Wagon(id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train_dict = train.model_dump()

        assert train_dict['train_id'] == '1'
        assert train_dict['arrival_time'] == test_date
        assert len(train_dict['wagons']) == 1
        assert train_dict['wagons'][0]['id'] == 'W001'

    def test_train_arrival_json_serialization(self) -> None:
        """
        Test train arrival JSON serialization.

        Notes
        -----
        Validates that Train instances can be serialized to JSON and that
        the resulting JSON string contains expected field values and can
        be parsed back to a dictionary.
        """
        wagons = [Wagon(id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        json_str = train.model_dump_json()

        # Should be valid JSON that can be parsed back
        parsed = json.loads(json_str)

        assert parsed['train_id'] == '1'
        assert parsed['arrival_time'].startswith('2024-01-15T00:00:00')
        assert len(parsed['wagons']) == 1

    def test_train_arrival_from_dict(self) -> None:
        """
        Test train arrival creation from dictionary.

        Notes
        -----
        Validates that Train instances can be created from dictionary data
        matching the structure of serialized Train objects, with proper
        datetime parsing.
        """
        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train_data = {
            'train_id': '1',
            'arrival_time': test_date.isoformat(),
            'wagons': [{'id': 'W001', 'train_id': '1', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}],
        }

        train = Train(**train_data)
        assert train.train_id == '1'
        assert train.arrival_time.date() == test_date.date()
        assert len(train.wagons) == 1
        assert train.wagons[0].id == 'W001'

    def test_train_arrival_realistic_scenarios(self) -> None:
        """
        Test train arrival with realistic scenario data.

        Notes
        -----
        Validates Train creation with realistic freight and maintenance
        train scenarios, including multiple wagons with varied properties
        and different arrival times.
        """
        # Early morning freight train
        freight_wagons = [
            Wagon(id='FREIGHT_001', length=20.0, is_loaded=True, needs_retrofit=False, train_id='FREIGHT_001'),
            Wagon(id='FREIGHT_002', length=20.0, is_loaded=True, needs_retrofit=True, train_id='FREIGHT_001'),
            Wagon(id='FREIGHT_003', length=18.5, is_loaded=False, needs_retrofit=False, train_id='FREIGHT_001'),
        ]

        test_date = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
        freight_train = Train(train_id='FREIGHT_001', arrival_time=test_date, wagons=freight_wagons)

        assert freight_train.train_id == 'FREIGHT_001'
        assert freight_train.arrival_time == test_date
        assert len(freight_train.wagons) == 3

        # Late night maintenance train
        maint_wagons = [
            Wagon(id='MAINT_001', length=12.0, is_loaded=False, needs_retrofit=True, train_id='MAINT_SPECIAL')
        ]

        main_arrival = test_date + timedelta(hours=8)
        main_train = Train(train_id='MAINT_SPECIAL', arrival_time=main_arrival, wagons=maint_wagons)

        assert main_train.train_id == 'MAINT_SPECIAL'
        assert main_train.wagons[0].needs_retrofit is True
