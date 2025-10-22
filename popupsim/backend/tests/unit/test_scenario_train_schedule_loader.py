import json
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from src.configuration.model import ScenarioConfig, TrainArrival
from src.configuration.service import ConfigurationError, ConfigurationService


class TestConfigurationService:
    """Test cases for ConfigurationService class."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ConfigurationService instance with temporary base path."""
        return ConfigurationService(base_path=tmp_path)

    @pytest.fixture
    def valid_scenario_data(self):
        """Valid scenario configuration data."""
        return {
            'scenario_id': 'test_scenario',
            'start_date': '2024-01-01',
            'end_date': '2024-01-09',
            'random_seed': 42,
            'train_schedule_file': 'schedule.csv',
        }

    @pytest.fixture
    def valid_csv_data(self):
        """Valid CSV data for train schedule."""
        return """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
        \nT001,2024-01-05,14:30,W001,12.5,True,False
        \nT001,2024-01-05,14:30,W002,10.0,False,True
        \nT002,2024-01-07,09:15,W003,15.0,True,False"""

    def test_service_initialization_default_path(self):
        """Test service initialization with default path."""
        service = ConfigurationService()
        assert service.base_path == Path.cwd()

    def test_service_initialization_custom_path(self, tmp_path):
        """Test service initialization with custom path."""
        service = ConfigurationService(base_path=tmp_path)
        assert service.base_path == tmp_path

    def test_load_scenario_from_directory(self, service, tmp_path, valid_scenario_data):
        """Test loading scenario from directory containing scenario.json."""
        scenario_file = tmp_path / 'scenario.json'
        scenario_file.write_text(json.dumps(valid_scenario_data))

        config = service.load_scenario(tmp_path)
        assert isinstance(config, ScenarioConfig)
        assert config.scenario_id == 'test_scenario'

    def test_load_scenario_from_file_path(self, service, tmp_path, valid_scenario_data):
        """Test loading scenario from direct file path."""
        scenario_file = tmp_path / 'test_scenario.json'
        scenario_file.write_text(json.dumps(valid_scenario_data))

        config = service.load_scenario(scenario_file)
        assert isinstance(config, ScenarioConfig)
        assert config.scenario_id == 'test_scenario'

    def test_load_scenario_file_not_found(self, service, tmp_path):
        """Test ConfigurationError when scenario file not found."""
        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(tmp_path / 'nonexistent')
        assert 'not found' in str(exc_info.value)

    def test_load_scenario_invalid_json(self, service, tmp_path):
        """Test ConfigurationError for invalid JSON."""
        scenario_file = tmp_path / 'scenario.json'
        scenario_file.write_text('{"invalid": json}')

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(tmp_path)
        assert 'Invalid JSON syntax' in str(exc_info.value)

    def test_load_scenario_missing_required_fields(self, service, tmp_path):
        """Test ConfigurationError for missing required fields."""
        incomplete_data = {'scenario_id': 'test'}
        scenario_file = tmp_path / 'scenario.json'
        scenario_file.write_text(json.dumps(incomplete_data))

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(tmp_path)
        assert 'Missing required fields' in str(exc_info.value)

    def test_load_scenario_validation_error(self, service, tmp_path):
        """Test ConfigurationError for validation errors."""
        invalid_data = {
            'scenario_id': '',  # Invalid: empty string
            'start_date': '2024-01-01',
            'end_date': '2024-01-09',
            'train_schedule_file': 'schedule.csv',
        }
        scenario_file = tmp_path / 'scenario.json'
        scenario_file.write_text(json.dumps(invalid_data))

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(tmp_path)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_and_validate_scenario_success(self, service, tmp_path, valid_scenario_data):
        """Test successful scenario loading with file validation."""
        scenario_file = tmp_path / 'scenario.json'
        schedule_file = tmp_path / 'schedule.csv'
        scenario_file.write_text(json.dumps(valid_scenario_data))
        schedule_file.write_text('dummy content')
        # load_and_validate_scenario requires scenario and train schedule files
        config = service.load_and_validate_scenario(tmp_path)
        assert isinstance(config, ScenarioConfig)
        assert config.scenario_id == 'test_scenario'

    def test_load_and_validate_scenario_missing_schedule_file(self, service, tmp_path, valid_scenario_data):
        """Test ConfigurationError when referenced schedule file missing."""
        scenario_file = tmp_path / 'scenario.json'
        scenario_file.write_text(json.dumps(valid_scenario_data))
        # Note: schedule.csv is not created

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_and_validate_scenario(tmp_path)
        assert 'Train schedule file not found' in str(exc_info.value)

    def test_load_train_schedule_success(self, service, tmp_path, valid_csv_data):
        """Test successful train schedule loading."""
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text(valid_csv_data)

        trains = service.load_train_schedule(schedule_file)
        assert len(trains) == 2
        assert isinstance(trains[0], TrainArrival)
        assert trains[0].train_id == 'T001'
        assert len(trains[0].wagons) == 2

    def test_load_train_schedule_file_not_found(self, service, tmp_path):
        """Test ConfigurationError when schedule file not found."""
        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(tmp_path / 'schedule.csv')
        assert 'not found' in str(exc_info.value)

    def test_load_train_schedule_empty_file(self, service, tmp_path):
        """Test ConfigurationError for empty CSV file."""
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text('')

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'empty' in str(exc_info.value)

    def test_load_train_schedule_missing_columns(self, service, tmp_path):
        """Test ConfigurationError for missing required columns."""
        incomplete_csv = 'train_id,arrival_date\nT001,2024-01-15'
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text(incomplete_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'Missing required columns' in str(exc_info.value)

    def test_load_train_schedule_duplicate_wagons(self, service, tmp_path):
        """Test ConfigurationError for duplicate wagon IDs. Wagon already completed can not carry status undone in future"""
        duplicate_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
        T001,2024-01-15,14:30,W001,12.5,True,False
        T002,2024-01-16,09:15,W001,10.0,False,True
        """
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text(duplicate_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'Duplicate wagon IDs' in str(exc_info.value)

    def test_load_train_schedule_inconsistent_arrival_times(self, service, tmp_path):
        """Test ConfigurationError for inconsistent arrival times within a train."""
        inconsistent_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
        T001,2024-01-15,14:30,W001,12.5,True,False
        T001,2024-01-15,15:30,W002,10.0,False,True
        """
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text(inconsistent_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'inconsistent arrival date/time' in str(exc_info.value)

    def test_load_complete_scenario_success(self, service, tmp_path, valid_scenario_data, valid_csv_data):
        """Test successful complete scenario loading."""
        scenario_file = tmp_path / 'scenario.json'
        schedule_file = tmp_path / 'schedule.csv'
        scenario_file.write_text(json.dumps(valid_scenario_data))
        schedule_file.write_text(valid_csv_data)

        config, trains = service.load_complete_scenario(tmp_path)
        assert isinstance(config, ScenarioConfig)
        assert len(trains) == 2
        assert config.scenario_id == 'test_scenario'

    def test_load_complete_scenario_trains_outside_date_range(self, service, tmp_path):
        """Test ConfigurationError when trains arrive outside scenario date range."""
        # Scenario with narrow date range
        narrow_scenario = {
            'scenario_id': 'test_scenario',
            'start_date': '2024-01-01',
            'end_date': '2024-01-10',  # Trains arrive on 2024-01-15 and 2024-01-16
            'train_schedule_file': 'schedule.csv',
        }

        scenario_file = tmp_path / 'scenario.json'
        schedule_file = tmp_path / 'schedule.csv'
        scenario_file.write_text(json.dumps(narrow_scenario))
        # Provide CSV data with train arrivals outside the scenario date range
        out_of_range_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\nT001,2024-01-15,14:30,W001,12.5,True,False\nT002,2024-01-16,09:15,W002,10.0,False,True"""
        schedule_file.write_text(out_of_range_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_complete_scenario(tmp_path)
        assert 'outside scenario date range' in str(exc_info.value)

    def test_read_and_validate_csv_parser_error(self, service, tmp_path):
        """Test ConfigurationError for CSV parser errors."""
        malformed_csv = """
        train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
        T001,2024-01-15,14:30,W001,12.5,True,False,ExtraColumn
        """
        schedule_file = tmp_path / 'schedule.csv'
        schedule_file.write_text(malformed_csv)
        # ExtraColumn is not expected
        with pytest.raises(ConfigurationError) as exc_info:
            service._read_and_validate_csv(schedule_file)
        assert 'Missing required columns' in str(exc_info.value)

    def test_create_train_arrivals_invalid_time_format(self, service):
        """Test ConfigurationError for invalid time format."""
        df = pd.DataFrame(
            {
                'train_id': ['T001'],
                'arrival_date': [pd.Timestamp('2024-01-15')],
                'arrival_time': ['25:30'],  # Invalid time
                'wagon_id': ['W001'],
                'length': [12.5],
                'is_loaded': [True],
                'needs_retrofit': [False],
            }
        )

        with pytest.raises(ConfigurationError) as exc_info:
            service._create_train_arrivals(df)
        assert 'Invalid time format' in str(exc_info.value)

    def test_create_wagons_from_group_validation_error(self, service):
        """Test ConfigurationError when wagon validation fails."""
        df = pd.DataFrame(
            {
                'train_id': ['T001'],
                'wagon_id': ['W001'],
                'length': [-5.0],  # Invalid: negative length
                'is_loaded': [True],
                'needs_retrofit': [False],
            }
        )

        with pytest.raises(ConfigurationError) as exc_info:
            service._create_wagons_from_group(df)
        assert 'Validation failed for wagon' in str(exc_info.value)

    def test_read_and_validate_csv_not_dataframe(self, service, tmp_path, monkeypatch):
        """Test ConfigurationError if pandas.read_csv does not return a DataFrame."""

        dummy_csv = tmp_path / 'schedule.csv'
        dummy_csv.write_text('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
        # Use monkeypatch to replace pd.read_csv with a function returning None
        monkeypatch.setattr(pd, 'read_csv', lambda *_a, **_k: None)
        with pytest.raises(ConfigurationError) as exc_info:
            service._read_and_validate_csv(dummy_csv)
        assert 'not a pandas DataFrame' in str(exc_info.value)

    def test_read_and_validate_csv_success(self, service, tmp_path, monkeypatch):
        """Test successful DataFrame loading with all required columns."""

        dummy_csv = tmp_path / 'schedule.csv'
        dummy_csv.write_text('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
        # Create a valid DataFrame with all required columns
        df_mock = pd.DataFrame(
            {
                'train_id': ['T001'],
                'arrival_date': [pd.Timestamp('2024-01-15')],
                'arrival_time': ['14:30'],
                'wagon_id': ['W001'],
                'length': [12.5],
                'is_loaded': [True],
                'needs_retrofit': [False],
            }
        )
        monkeypatch.setattr(pd, 'read_csv', lambda *_a, **_k: df_mock)
        result = service._read_and_validate_csv(dummy_csv)
        assert isinstance(result, pd.DataFrame)
        assert result.equals(df_mock)

    def test_train_arrival_with_wagons(self):
        from src.configuration.model import WagonInfo

        ta = TrainArrival(
            train_id='T1',
            arrival_date='2024-01-01',
            arrival_time='12:00',
            wagons=[WagonInfo(wagon_id='W1', length=10.0, is_loaded=True, needs_retrofit=False)],
        )
        assert ta.train_id == 'T1'
        assert ta.wagons[0].wagon_id == 'W1'

    def test_train_arrival_without_wagons(self):
        with pytest.raises(ValidationError) as exc_info:
            TrainArrival(train_id='T2', arrival_date='2024-01-01', arrival_time='12:00', wagons=[])
        # Check for custom error message from validator
        assert 'must have at least one wagon' in str(exc_info.value)
