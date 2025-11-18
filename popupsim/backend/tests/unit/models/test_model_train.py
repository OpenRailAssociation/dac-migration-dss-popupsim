"""
Unit tests for Train model.

Tests the Train model validation logic, time parsing,
wagon validation, and datetime combination functionality.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
import json
from pathlib import Path

from builders.scenario_builder import BuilderError
from builders.scenario_builder import ScenarioBuilder
from models.train import Train
from models.wagon import Wagon
from pydantic import ValidationError
import pytest


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
            Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1'),
            Wagon(wagon_id='W002', length=12.0, is_loaded=False, needs_retrofit=True, train_id='1'),
        ]
        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        assert train.train_id == '1'
        assert train.arrival_time == test_date
        assert len(train.wagons) == 2
        assert train.wagons[0].wagon_id == 'W001'

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
        wagon = Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=[wagon])

        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

    def test_train_arrival_equality(self) -> None:
        """
        Test train arrival equality comparison.

        Notes
        -----
        Validates that Train instances with identical field values are
        considered equal, while instances with different values are not.
        """
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

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
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

        test_date = datetime(2024, 1, 15, tzinfo=UTC)
        train = Train(train_id='1', arrival_time=test_date, wagons=wagons)

        train_dict = train.model_dump()

        assert train_dict['train_id'] == '1'
        assert train_dict['arrival_time'] == test_date
        assert len(train_dict['wagons']) == 1
        assert train_dict['wagons'][0]['wagon_id'] == 'W001'

    def test_train_arrival_json_serialization(self) -> None:
        """
        Test train arrival JSON serialization.

        Notes
        -----
        Validates that Train instances can be serialized to JSON and that
        the resulting JSON string contains expected field values and can
        be parsed back to a dictionary.
        """
        wagons = [Wagon(wagon_id='W001', length=15.5, is_loaded=True, needs_retrofit=False, train_id='1')]

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
            'wagons': [
                {'wagon_id': 'W001', 'train_id': '1', 'length': 15.5, 'is_loaded': True, 'needs_retrofit': False}
            ],
        }

        train = Train(**train_data)
        assert train.train_id == '1'
        assert train.arrival_time.date() == test_date.date()
        assert len(train.wagons) == 1
        assert train.wagons[0].wagon_id == 'W001'

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
            Wagon(wagon_id='FREIGHT_001', length=20.0, is_loaded=True, needs_retrofit=False, train_id='FREIGHT_001'),
            Wagon(wagon_id='FREIGHT_002', length=20.0, is_loaded=True, needs_retrofit=True, train_id='FREIGHT_001'),
            Wagon(wagon_id='FREIGHT_003', length=18.5, is_loaded=False, needs_retrofit=False, train_id='FREIGHT_001'),
        ]

        test_date = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
        freight_train = Train(train_id='FREIGHT_001', arrival_time=test_date, wagons=freight_wagons)

        assert freight_train.train_id == 'FREIGHT_001'
        assert freight_train.arrival_time == test_date
        assert len(freight_train.wagons) == 3

        # Late night maintenance train
        maint_wagons = [
            Wagon(wagon_id='MAINT_001', length=12.0, is_loaded=False, needs_retrofit=True, train_id='MAINT_SPECIAL')
        ]

        main_arrival = test_date + timedelta(hours=8)
        main_train = Train(train_id='MAINT_SPECIAL', arrival_time=main_arrival, wagons=maint_wagons)

        assert main_train.train_id == 'MAINT_SPECIAL'
        assert main_train.wagons[0].needs_retrofit is True


class TestTrainScheduleCSVLoading:
    """Test cases for loading train schedules from CSV files."""

    @pytest.fixture
    def config_service(self) -> ScenarioBuilder:
        """
        Return a ConfigurationService instance for testing.

        Returns
        -------
        ScenarioBuilder
            Service instance for models loading and validation.
        """
        return ScenarioBuilder()

    @pytest.fixture
    def valid_csv_path(self) -> Path:
        """
        Return path to valid test CSV file.

        Returns
        -------
        Path
            Path to the test train schedule CSV fixture.
        """
        return Path(__file__).parent.parent / 'fixtures' / 'config' / 'test_train_schedule.csv'

    @pytest.fixture
    def invalid_csv_path(self) -> Path:
        """
        Return path to invalid test CSV file.

        Returns
        -------
        Path
            Path to the invalid train schedule CSV fixture.
        """
        return Path(__file__).parent.parent / 'fixtures' / 'config' / 'test_train_schedule_invalid.csv'

    # TODO: clarify if neededdecide how to chain Scenario with Train Shedule
    # def test_load_train_schedule_csv_success(self, config_service: ScenarioBuilder, valid_csv_path: Path) -> None:
    #     """
    #     Test successful loading of train schedule from valid CSV file.
    #
    #     Parameters
    #     ----------
    #     config_service : ScenarioBuilder
    #         Configuration service instance.
    #     valid_csv_path : Path
    #         Path to valid test CSV file.
    #
    #     Notes
    #     -----
    #     Validates that train schedules can be loaded from CSV files with
    #     correct parsing of train IDs, wagon details, and all required fields.
    #     """
    #     trains: list[Train] = config_service.load_train_schedule(valid_csv_path)
    #
    #     # Verify we got a list of Train objects
    #     assert isinstance(trains, list)
    #     assert len(trains) > 0
    #     assert all(isinstance(t, Train) for t in trains)
    #
    #     # Test train_id '1' exists and has correct number of wagons
    #     train_1: Train | None = next((t for t in trains if t.train_id == '1'), None)
    #     assert train_1 is not None
    #     assert len(train_1.wagons) >= 1
    #
    #     # Verify wagon IDs for train '1'
    #     wagon_ids: list[str] = [w.wagon_id for w in train_1.wagons]
    #     assert '874' in wagon_ids
    #     assert '855' in wagon_ids
    #     assert '841' in wagon_ids
    #
    #     # Verify wagon details for wagon '874'
    #     wagon_874: Wagon | None = next((w for w in train_1.wagons if w.wagon_id == '874'), None)
    #     assert wagon_874 is not None
    #     assert wagon_874.length >= 0.0
    #     assert isinstance(wagon_874.is_loaded, bool)
    #     assert isinstance(wagon_874.needs_retrofit, bool)

    def test_load_train_schedule_csv_nonexistent_file(self, config_service: ScenarioBuilder) -> None:
        """
        Test error handling when CSV file does not exist.

        Parameters
        ----------
        config_service : ScenarioBuilder
            Configuration service instance.

        Notes
        -----
        Validates that attempting to load from non-existent file raises
        ConfigurationError with appropriate message.
        """
        nonexistent_path = Path('/nonexistent/path/train_schedule.csv')

        with pytest.raises(BuilderError) as exc_info:
            config_service.load_train_schedule(nonexistent_path)

        assert 'Train schedule file not found' in str(exc_info.value)

    def test_load_train_schedule_csv_empty_file(self, config_service: ScenarioBuilder, tmp_path: Path) -> None:
        """
        Test error handling when CSV file is empty.

        Parameters
        ----------
        config_service : ScenarioBuilder
            Configuration service instance.
        tmp_path : Path
            Pytest temporary directory fixture.

        Notes
        -----
        Validates that completely empty CSV files raise ConfigurationError
        during loading with appropriate error message.
        """
        empty_csv = tmp_path / 'empty_train_schedule.csv'
        empty_csv.write_text('')

        with pytest.raises(BuilderError) as exc_info:
            config_service.load_train_schedule(empty_csv)

        # The actual error message for completely empty files
        assert 'Unexpected error loading train schedule' in str(exc_info.value)
