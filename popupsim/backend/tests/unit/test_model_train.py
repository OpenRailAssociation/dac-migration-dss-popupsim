"""
Unit tests for Train model.

Tests the Train model validation logic, time parsing,
wagon validation, and datetime combination functionality.
"""

from datetime import datetime
from datetime import time
from datetime import timedelta
from pathlib import Path

from pydantic import ValidationError
import pytest

from configuration.model_train import Train
from configuration.model_wagon import Wagon
from configuration.service import ConfigurationError
from configuration.service import ConfigurationService


class TestTrain:
    """Test cases for Train model."""

    def test_train_arrival_creation_valid_data(self) -> None:
        """Test successful train arrival creation with valid data."""
        wagons = [
            Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1'),
            Wagon(wagon_id='W002', length=12.0, is_loaded=False, needs_retrofit=True, train_id='1'),
        ]
        test_date = datetime(2024, 1, 15)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        assert train.train_id == '1'
        assert train.arrival_time == test_date
        assert len(train.wagons) == 2
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_empty_wagons_validation(self) -> None:
        """Test validation error when wagons list is empty."""
        test_date = datetime(2024, 1, 15)
        with pytest.raises(ValidationError) as exc_info:
            Train(train_id='1', arrival_time=test_date, wagons=[])
        assert 'must have at least one wagon' in str(exc_info.value)

    def test_train_arrival_missing_wagons_field(self) -> None:
        """Test validation error when wagons field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            Train(train_id='1', arrival_time=time(8, 30))
        assert 'Field required' in str(exc_info.value)

    def test_train_arrival_single_wagon(self) -> None:
        """Test train arrival with single wagon."""
        wagon = Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')

        test_date = datetime(2024, 1, 15)
        train = Train(train_id='1', arrival_time=test_date, wagons=[wagon])

        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_equality(self) -> None:
        """Test train arrival equality comparison."""
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15)
        train1 = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train2 = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train3 = Train(train_id='TRAIN002', arrival_time=test_date + timedelta(days=1), wagons=wagons)

        assert train1 == train2
        assert train1 != train3

    def test_train_arrival_dict_conversion(self) -> None:
        """Test train arrival conversion to dictionary."""
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train_dict = train.model_dump()

        assert train_dict['train_id'] == '1'
        assert train_dict['arrival_time'] == test_date
        assert len(train_dict['wagons']) == 1
        assert train_dict['wagons'][0]['wagon_id'] == 'W001'

    def test_train_arrival_json_serialization(self) -> None:
        """Test train arrival JSON serialization."""
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        json_str = train.model_dump_json()

        # Should be valid JSON that can be parsed back
        import json

        parsed = json.loads(json_str)

        assert parsed['train_id'] == '1'
        assert parsed['arrival_time'] == '2024-01-15T00:00:00'
        assert len(parsed['wagons']) == 1

    def test_train_arrival_from_dict(self) -> None:
        """Test train arrival creation from dictionary."""
        test_date = datetime(2024, 1, 15)
        train_data = {
            'train_id': '1',
            'arrival_time': str(test_date),
            'wagons': [
                {'wagon_id': 'W001', 'train_id': '1', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}
            ],
        }

        train = Train(**train_data)
        assert train.train_id == '1'
        assert train.arrival_time == test_date
        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_realistic_scenarios(self) -> None:
        """Test train arrival with realistic scenario data."""
        # Early morning freight train
        freight_wagons = [
            Wagon(wagon_id='FREIGHT_001', length=20.0, is_loaded=True, needs_retrofit=False, train_id='FREIGHT_001'),
            Wagon(wagon_id='FREIGHT_002', length=20.0, is_loaded=True, needs_retrofit=True, train_id='FREIGHT_001'),
            Wagon(wagon_id='FREIGHT_003', length=18.5, is_loaded=False, needs_retrofit=False, train_id='FREIGHT_001'),
        ]

        test_date = datetime(2024, 1, 15, 12, 0)
        freight_train = Train(train_id='FREIGHT_001', arrival_time=test_date, wagons=freight_wagons)

        assert freight_train.train_id == 'FREIGHT_001'
        assert freight_train.arrival_time == test_date
        assert len(freight_train.wagons) == 3

        # Late night maintenance train
        maint_wagons = [
            Wagon(wagon_id='MAINT_001', length=12.0, is_loaded=False, needs_retrofit=True, train_id='MAINT_SPECIAL')
        ]

        maint_train = Train(
            train_id='MAINT_SPECIAL',
            arrival_date=test_date,
            arrival_time=test_date + timedelta(hours=8),
            wagons=maint_wagons,
        )

        assert maint_train.train_id == 'MAINT_SPECIAL'
        assert maint_train.wagons[0].needs_retrofit is True


class TestTrainScheduleCSVLoading:
    """Test cases for loading train schedules from CSV files."""

    @pytest.fixture
    def config_service(self) -> ConfigurationService:
        """Return a ConfigurationService instance for testing."""
        return ConfigurationService()

    @pytest.fixture
    def valid_csv_path(self) -> Path:
        """Return path to valid test CSV file."""
        return Path(__file__).parent.parent / 'fixtures' / 'config' / 'test_train_schedule.csv'

    @pytest.fixture
    def invalid_csv_path(self) -> Path:
        """Return path to invalid test CSV file."""
        return Path(__file__).parent.parent / 'fixtures' / 'config' / 'test_train_schedule_invalid.csv'

    def test_load_train_schedule_csv_success(self, config_service: ConfigurationService, valid_csv_path: Path) -> None:
        """Test successful loading of train schedule from valid CSV file."""
        trains: list[Train] = config_service.load_train_schedule(valid_csv_path)

        # Verify we got a list of Train objects
        assert isinstance(trains, list)
        assert len(trains) > 0
        assert all(isinstance(t, Train) for t in trains)

        # Test train_id '1' exists and has correct number of wagons
        train_1: Train | None = next((t for t in trains if t.train_id == '1'), None)
        assert train_1 is not None
        assert len(train_1.wagons) >= 1

        # Verify wagon IDs for train '1'
        wagon_ids: list[str] = [w.wagon_id for w in train_1.wagons]
        assert '874' in wagon_ids
        assert '855' in wagon_ids
        assert '841' in wagon_ids

        # Verify wagon details for wagon '874'
        wagon_874: Wagon | None = next((w for w in train_1.wagons if w.wagon_id == '874'), None)
        assert wagon_874 is not None
        assert wagon_874.length >= 0.0
        assert isinstance(wagon_874.is_loaded, bool)
        assert isinstance(wagon_874.needs_retrofit, bool)

    def test_load_train_schedule_csv_nonexistent_file(self, config_service: ConfigurationService) -> None:
        """Test error handling when CSV file does not exist."""
        nonexistent_path = Path('/nonexistent/path/train_schedule.csv')

        with pytest.raises(ConfigurationError) as exc_info:
            config_service.load_train_schedule(nonexistent_path)

        assert 'Train schedule file not found' in str(exc_info.value)

    def test_load_train_schedule_csv_empty_file(self, config_service: ConfigurationService, tmp_path: Path) -> None:
        """Test error handling when CSV file is empty."""
        empty_csv = tmp_path / 'empty_train_schedule.csv'
        empty_csv.write_text('')

        with pytest.raises(ConfigurationError) as exc_info:
            config_service.load_train_schedule(empty_csv)

        # The actual error message for completely empty files
        assert 'Unexpected error loading train schedule' in str(exc_info.value)
