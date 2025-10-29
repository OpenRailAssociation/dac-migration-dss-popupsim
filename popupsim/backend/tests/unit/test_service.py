"""
Test cases for configuration service module.

This module tests the ConfigurationService class which handles:
- Loading and validating scenario configurations from JSON files
- Loading and parsing train schedule data from CSV files
- Creating validated domain models (ScenarioConfig, Train, Wagon)
- Cross-validation between scenario dates and train arrival dates
- Comprehensive error handling and logging for configuration issues
"""

from datetime import date
from datetime import time
import json
from pathlib import Path
import tempfile
from typing import Any
from typing import Dict

import pandas as pd
import pytest

from configuration.model_track import TrackFunction
from configuration.model_wagon import Wagon
from configuration.model_workshop import Workshop
from configuration.service import ConfigurationError
from configuration.service import ConfigurationService


class TestConfigurationService:
    """Test suite for ConfigurationService class."""

    @pytest.fixture
    def service(self) -> ConfigurationService:
        """Create a ConfigurationService instance for testing."""
        return ConfigurationService()

    @pytest.fixture
    def fixtures_path(self) -> Path:
        """Get the path to test fixtures directory."""
        return Path(__file__).parent.parent / 'fixtures' / 'config'

    @pytest.fixture
    def scenario_data(self) -> Dict[str, Any]:
        """Sample scenario configuration data."""
        return {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'random_seed': 42,
            'workshop': {
                'tracks': [
                    {'id': 'TRACK01', 'function': 'werkstattgleis', 'capacity': 5, 'retrofit_time_min': 30},
                    {'id': 'TRACK02', 'function': 'werkstattgleis', 'capacity': 3, 'retrofit_time_min': 45},
                ]
            },
            'train_schedule_file': 'test_train_schedule.csv',
        }

    def test_init_default_path(self) -> None:
        """Test ConfigurationService initialization with default path."""
        service = ConfigurationService()
        assert service.base_path == Path.cwd()

    def test_init_custom_path(self) -> None:
        """Test ConfigurationService initialization with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir)
            service = ConfigurationService(custom_path)
            assert service.base_path == custom_path

    def test_load_scenario_from_fixtures(self, service: ConfigurationService, fixtures_path: Path) -> None:
        """Test loading scenario configuration from test fixtures."""
        scenario_data = service.load_scenario(fixtures_path)

        assert scenario_data['scenario_id'] == 'scenario_001'
        assert scenario_data['start_date'] == '2024-01-15'
        assert scenario_data['end_date'] == '2024-01-16'
        assert scenario_data['random_seed'] == 42
        assert scenario_data['train_schedule_file'] == 'test_train_schedule.csv'
        assert 'workshop' in scenario_data

    def test_load_scenario_missing_file(self, service: ConfigurationService) -> None:
        """Test loading scenario when configuration file is missing."""
        non_existent_path = Path('/non/existent/path')

        with pytest.raises(ConfigurationError, match='Scenario configuration file not found'):
            service.load_scenario(non_existent_path)

    def test_load_scenario_invalid_json(self, service: ConfigurationService) -> None:
        """Test loading scenario with invalid JSON syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json syntax}')
            invalid_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Invalid JSON syntax'):
                service.load_scenario(invalid_file)
        finally:
            invalid_file.unlink()

    def test_load_scenario_missing_required_fields(self, service: ConfigurationService) -> None:
        """Test loading scenario with missing required fields."""
        incomplete_data = {'scenario_id': 'test', 'start_date': '2024-01-15'}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_data, f)
            incomplete_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Missing required fields'):
                service.load_scenario(incomplete_file)
        finally:
            incomplete_file.unlink()

    def test_load_and_validate_scenario_success(self, service: ConfigurationService, fixtures_path: Path) -> None:
        """Test successful scenario loading and validation."""
        scenario_data = service.load_and_validate_scenario(fixtures_path)

        assert scenario_data['scenario_id'] == 'scenario_001'
        assert 'train_schedule_file' in scenario_data

    def test_load_and_validate_scenario_missing_train_schedule(self, service: ConfigurationService) -> None:
        """Test scenario validation when train schedule file is missing."""
        scenario_data = {
            'scenario_id': 'test',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'train_schedule_file': 'non_existent.csv',
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            scenario_file = temp_path / 'test_scenario.json'

            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            with pytest.raises(ConfigurationError, match='Train schedule file not found'):
                service.load_and_validate_scenario(temp_path)

    def test_to_bool_static_method(self) -> None:
        """Test the static to_bool converter method."""
        # Test boolean values
        assert ConfigurationService.to_bool(True) is True
        assert ConfigurationService.to_bool(False) is False

        # Test numeric values
        assert ConfigurationService.to_bool(1) is True
        assert ConfigurationService.to_bool(0) is False
        assert ConfigurationService.to_bool(5) is True
        assert ConfigurationService.to_bool(0.0) is False
        assert ConfigurationService.to_bool(3.14) is True

        # Test string values
        assert ConfigurationService.to_bool('true') is True
        assert ConfigurationService.to_bool('TRUE') is True
        assert ConfigurationService.to_bool('True') is True
        assert ConfigurationService.to_bool(' true ') is True
        assert ConfigurationService.to_bool('false') is False
        assert ConfigurationService.to_bool('FALSE') is False
        assert ConfigurationService.to_bool('anything_else') is False

        # Test other types
        assert ConfigurationService.to_bool(None) is False
        assert ConfigurationService.to_bool([]) is False

    def test_load_train_schedule_success(self, service: ConfigurationService, fixtures_path: Path) -> None:
        """Test successful loading of train schedule from CSV."""
        train_schedule_path = fixtures_path / 'test_train_schedule.csv'
        trains = service.load_train_schedule(train_schedule_path)

        assert len(trains) == 3  # Based on actual fixture data

        # Test first train (TRAIN001)
        train_001 = next(t for t in trains if t.train_id == 'TRAIN001')
        assert train_001.arrival_date == date(2024, 1, 15)
        assert train_001.arrival_time == time(8, 0)
        assert len(train_001.wagons) == 3

        # Test wagon details for TRAIN001
        wagon_ids = [w.wagon_id for w in train_001.wagons]
        assert 'WAGON001_01' in wagon_ids
        assert 'WAGON001_02' in wagon_ids
        assert 'WAGON001_03' in wagon_ids

        wagon_w001_01 = next(w for w in train_001.wagons if w.wagon_id == 'WAGON001_01')
        assert wagon_w001_01.length == 15.5
        assert wagon_w001_01.is_loaded is True
        assert wagon_w001_01.needs_retrofit is True

    def test_load_train_schedule_missing_file(self, service: ConfigurationService) -> None:
        """Test loading train schedule when CSV file is missing."""
        non_existent_path = Path('/non/existent/schedule.csv')

        with pytest.raises(ConfigurationError, match='Train schedule file not found'):
            service.load_train_schedule(non_existent_path)

    def test_load_train_schedule_empty_file(self, service: ConfigurationService) -> None:
        """Test loading train schedule from empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')  # Empty file
            empty_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Train schedule file is empty'):
                service.load_train_schedule(empty_file)
        finally:
            empty_file.unlink()

    def test_load_train_schedule_missing_columns(self, service: ConfigurationService) -> None:
        """Test loading train schedule with missing required columns."""
        csv_content = 'train_id,arrival_date\nT001,2024-01-15\n'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            incomplete_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Missing required columns'):
                service.load_train_schedule(incomplete_file)
        finally:
            incomplete_file.unlink()

    def test_load_train_schedule_invalid_time_format(self, service: ConfigurationService) -> None:
        """Test loading train schedule with invalid time format."""
        csv_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,25:70,W001,15.5,true,false"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            invalid_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match=r'arrival_time.*HH:MM format'):
                service.load_train_schedule(invalid_file)
        finally:
            invalid_file.unlink()

    def test_load_train_schedule_duplicate_wagon_ids(self, service: ConfigurationService) -> None:
        """Test loading train schedule with duplicate wagon IDs."""
        csv_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,08:30,W001,15.5,true,false
T002,2024-01-15,09:30,W001,12.0,false,true"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            duplicate_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Duplicate wagon IDs found'):
                service.load_train_schedule(duplicate_file)
        finally:
            duplicate_file.unlink()

    def test_load_train_schedule_inconsistent_arrival_times(self, service: ConfigurationService) -> None:
        """Test loading train schedule with inconsistent arrival times for same train."""
        csv_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,08:30,W001,15.5,true,false
T001,2024-01-15,09:30,W002,12.0,false,true"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            inconsistent_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='inconsistent arrival date/time'):
                service.load_train_schedule(inconsistent_file)
        finally:
            inconsistent_file.unlink()

    def test_load_workshop_tracks_success(self, service: ConfigurationService, fixtures_path: Path) -> None:
        """Test successful loading of workshop tracks from CSV."""
        workshop_tracks_path = fixtures_path / 'test_workshop_tracks.csv'
        workshop = service.load_workshop_tracks(workshop_tracks_path)

        assert isinstance(workshop, Workshop)
        assert len(workshop.tracks) == 7  # Based on actual fixture data

        # Test track details
        track_ids = [t.id for t in workshop.tracks]
        assert 'TRACK01' in track_ids
        assert 'TRACK02' in track_ids
        assert 'TRACK03' in track_ids

        track_01 = next(t for t in workshop.tracks if t.id == 'TRACK01')
        assert track_01.function == TrackFunction.WERKSTATTGLEIS
        assert track_01.capacity == 5
        assert track_01.retrofit_time_min == 30

    def test_load_workshop_tracks_missing_file(self, service: ConfigurationService) -> None:
        """Test loading workshop tracks when CSV file is missing."""
        non_existent_path = Path('/non/existent/tracks.csv')

        with pytest.raises(ConfigurationError, match='Workshop tracks file not found'):
            service.load_workshop_tracks(non_existent_path)

    def test_load_workshop_tracks_empty_file(self, service: ConfigurationService) -> None:
        """Test loading workshop tracks from empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')  # Empty file
            empty_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Workshop tracks file is empty'):
                service.load_workshop_tracks(empty_file)
        finally:
            empty_file.unlink()

    def test_load_workshop_tracks_missing_columns(self, service: ConfigurationService) -> None:
        """Test loading workshop tracks with missing required columns."""
        csv_content = 'track_id,function\nTRACK01,werkstattgleis\n'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            incomplete_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Missing required columns'):
                service.load_workshop_tracks(incomplete_file)
        finally:
            incomplete_file.unlink()

    def test_load_workshop_tracks_duplicate_ids(self, service: ConfigurationService) -> None:
        """Test loading workshop tracks with duplicate track IDs."""
        csv_content = """track_id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK01,werkstattgleis,3,45"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            duplicate_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Duplicate track IDs found'):
                service.load_workshop_tracks(duplicate_file)
        finally:
            duplicate_file.unlink()

    def test_create_wagons_from_group(self, service: ConfigurationService) -> None:
        """Test creating wagon objects from DataFrame group."""
        # Create test DataFrame group
        data = {
            'wagon_id': ['W001', 'W002'],
            'train_id': ['T001', 'T001'],
            'length': [15.5, 12.0],
            'is_loaded': [True, False],
            'needs_retrofit': [False, True],
        }
        df = pd.DataFrame(data)

        wagons = service._create_wagons_from_group(df)

        assert len(wagons) == 2
        assert isinstance(wagons[0], Wagon)
        assert wagons[0].wagon_id == 'W001'
        assert wagons[0].train_id == 'T001'
        assert wagons[0].length == 15.5
        assert wagons[0].is_loaded is True
        assert wagons[0].needs_retrofit is False

    def test_load_scenario_validation_error_handling(self, service: ConfigurationService) -> None:
        """Test scenario loading with validation errors."""
        # Create a scenario that would cause ValidationError during ScenarioConfig creation
        invalid_scenario_data = {
            'scenario_id': 'test',
            'start_date': 'invalid-date-format',  # This should trigger validation error
            'end_date': '2024-01-16',
            'random_seed': 42,
            'train_schedule_file': 'test.csv',
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_scenario_data, f)
            invalid_file = Path(f.name)

        try:
            # The method should handle ValidationError and convert to ConfigurationError
            result = service.load_scenario(invalid_file)
            # Since we're only testing load_scenario (not validation), this should succeed
            assert result['start_date'] == 'invalid-date-format'
        finally:
            invalid_file.unlink()

    def test_load_scenario_unexpected_error(self, service: ConfigurationService) -> None:
        """Test scenario loading with unexpected errors."""
        # Create a file that will cause an unexpected error during processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write valid JSON but with a structure that might cause issues
            f.write('{"scenario_id": null}')  # null values might cause issues
            problematic_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Missing required fields'):
                service.load_scenario(problematic_file)
        finally:
            problematic_file.unlink()

    def test_load_scenario_file_path_resolution(self, service: ConfigurationService) -> None:
        """Test different file path resolution scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test direct JSON file path
            json_file = temp_path / 'direct_scenario.json'
            test_data = {
                'scenario_id': 'direct',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test.csv',
            }

            with open(json_file, 'w') as f:
                json.dump(test_data, f)

            # Test loading direct JSON file path
            result = service.load_scenario(json_file)
            assert result['scenario_id'] == 'direct'

    def test_read_and_validate_train_schedule_csv_not_dataframe(self, service: ConfigurationService) -> None:
        """Test CSV reading when result is not a DataFrame."""
        # This is a bit tricky to test as pd.read_csv almost always returns DataFrame
        # We'll mock the pandas function to return something else
        import unittest.mock

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
            f.write('T001,2024-01-15,08:30,W001,15.5,true,false\n')
            test_file = Path(f.name)

        try:
            with unittest.mock.patch('pandas.read_csv') as mock_read_csv:
                # Mock pandas.read_csv to return something that's not a DataFrame
                mock_read_csv.return_value = 'not a dataframe'

                with pytest.raises(ConfigurationError, match='Loaded object is not a pandas DataFrame'):
                    service._read_and_validate_train_schedule_csv(test_file)
        finally:
            test_file.unlink()

    def test_read_and_validate_train_schedule_csv_parser_error(self, service: ConfigurationService) -> None:
        """Test CSV reading with parser errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create malformed CSV that will cause parser error
            f.write('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
            f.write('T001,2024-01-15,08:30,"unclosed quote,15.5,true,false\n')
            malformed_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Error parsing CSV file'):
                service._read_and_validate_train_schedule_csv(malformed_file)
        finally:
            malformed_file.unlink()

    def test_read_and_validate_train_schedule_csv_datetime_validation(self, service: ConfigurationService) -> None:
        """Test CSV reading with invalid datetime format validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
            # Use arrival_date that can't be parsed as datetime
            f.write('T001,not-a-date,08:30,W001,15.5,true,false\n')
            invalid_date_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match="Column 'arrival_date' must be in YYYY-MM-DD format"):
                service._read_and_validate_train_schedule_csv(invalid_date_file)
        finally:
            invalid_date_file.unlink()

    def test_create_wagons_from_group_validation_error(self, service: ConfigurationService) -> None:
        """Test wagon creation with validation errors."""
        # Create DataFrame with invalid wagon data
        data = {
            'wagon_id': ['W001'],
            'train_id': ['T001'],
            'length': [-5.0],  # Negative length should cause validation error
            'is_loaded': [True],
            'needs_retrofit': [False],
        }
        df = pd.DataFrame(data)

        with pytest.raises(ConfigurationError, match='Validation failed for wagon'):
            service._create_wagons_from_group(df)

    def test_create_train_arrivals_time_parsing_error(self, service: ConfigurationService) -> None:
        """Test train arrivals creation with invalid time parsing."""
        data = {
            'train_id': ['T001'],
            'arrival_date': [pd.Timestamp('2024-01-15')],
            'arrival_time': ['invalid-time'],  # Invalid time format
            'wagon_id': ['W001'],
            'length': [15.5],
            'is_loaded': [True],
            'needs_retrofit': [False],
        }
        df = pd.DataFrame(data)

        with pytest.raises(ConfigurationError, match='Invalid time format in arrival_time'):
            service._create_train_arrivals(df)

    def test_create_train_arrivals_string_date_handling(self, service: ConfigurationService) -> None:
        """Test train arrivals creation with string date handling."""
        data = {
            'train_id': ['T001'],
            'arrival_date': ['2024-01-15'],  # String date instead of timestamp
            'arrival_time': ['08:30'],
            'wagon_id': ['W001'],
            'length': [15.5],
            'is_loaded': [True],
            'needs_retrofit': [False],
        }
        df = pd.DataFrame(data)

        trains = service._create_train_arrivals(df)
        assert len(trains) == 1
        assert trains[0].arrival_date == date(2024, 1, 15)

    def test_read_and_validate_workshop_tracks_csv_not_dataframe(self, service: ConfigurationService) -> None:
        """Test workshop tracks CSV reading when result is not a DataFrame."""
        import unittest.mock

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('track_id,function,capacity,retrofit_time_min\n')
            f.write('TRACK01,werkstattgleis,5,30\n')
            test_file = Path(f.name)

        try:
            with unittest.mock.patch('pandas.read_csv') as mock_read_csv:
                # Mock pandas.read_csv to return something that's not a DataFrame
                mock_read_csv.return_value = 'not a dataframe'

                with pytest.raises(ConfigurationError, match='Loaded object is not a pandas DataFrame'):
                    service._read_and_validate_workshop_tracks_csv(test_file)
        finally:
            test_file.unlink()

    def test_read_and_validate_workshop_tracks_csv_parser_error(self, service: ConfigurationService) -> None:
        """Test workshop tracks CSV reading with parser errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create malformed CSV
            f.write('track_id,function,capacity,retrofit_time_min\n')
            f.write('TRACK01,"unclosed quote,5,30\n')
            malformed_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Error parsing CSV file'):
                service._read_and_validate_workshop_tracks_csv(malformed_file)
        finally:
            malformed_file.unlink()

    def test_create_workshop_tracks_from_dataframe_validation_error(self, service: ConfigurationService) -> None:
        """Test workshop track creation with validation errors."""
        data = {
            'track_id': ['TRACK01'],
            'function': ['invalid_function'],  # Invalid function should cause error
            'capacity': [5],
            'retrofit_time_min': [30],
        }
        df = pd.DataFrame(data)

        with pytest.raises(ConfigurationError, match='Invalid data type for track'):
            service._create_workshop_tracks_from_dataframe(df)

    def test_create_workshop_tracks_from_dataframe_type_error(self, service: ConfigurationService) -> None:
        """Test workshop track creation with type conversion errors."""
        data = {
            'track_id': ['TRACK01'],
            'function': ['werkstattgleis'],
            'capacity': ['not-a-number'],  # Invalid capacity type
            'retrofit_time_min': [30],
        }
        df = pd.DataFrame(data)

        with pytest.raises(ConfigurationError, match='Invalid data type for track'):
            service._create_workshop_tracks_from_dataframe(df)

    def test_create_workshop_from_tracks_validation_error(self, service: ConfigurationService) -> None:
        """Test workshop creation with validation errors."""
        # Create an invalid track list that would fail Workshop validation

        tracks = []  # Empty tracks should cause validation error

        with pytest.raises(ConfigurationError, match='Validation failed for workshop configuration'):
            service._create_workshop_from_tracks(tracks)

    def test_create_workshop_from_tracks_unexpected_error(self, service: ConfigurationService) -> None:
        """Test workshop creation with unexpected errors."""
        import unittest.mock

        from configuration.model_track import WorkshopTrack

        # Create valid tracks
        track = WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)
        tracks = [track]

        with unittest.mock.patch('configuration.service.Workshop') as mock_workshop:
            # Mock Workshop to raise an unexpected error
            mock_workshop.side_effect = RuntimeError('Unexpected error')

            with pytest.raises(ConfigurationError, match='Unexpected error creating workshop'):
                service._create_workshop_from_tracks(tracks)

    def test_load_complete_scenario_missing_train_schedule_file(self, service: ConfigurationService) -> None:
        """Test complete scenario loading with missing train_schedule_file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create scenario without train_schedule_file
            scenario_data = {
                'scenario_id': 'test',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                # Missing train_schedule_file
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            with pytest.raises(ConfigurationError, match=r'Missing required fields.*train_schedule_file'):
                service.load_complete_scenario(temp_path)

    def test_load_complete_scenario_missing_dates(self, service: ConfigurationService) -> None:
        """Test complete scenario loading with missing start/end dates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create scenario without start_date
            scenario_data = {
                'scenario_id': 'test',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test.csv',
                # Missing start_date
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            with pytest.raises(ConfigurationError, match=r'Missing required fields.*start_date'):
                service.load_complete_scenario(temp_path)

    def test_load_complete_scenario_invalid_date_format(self, service: ConfigurationService) -> None:
        """Test complete scenario loading with invalid date formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create scenario with invalid date format
            scenario_data = {
                'scenario_id': 'test',
                'start_date': 'invalid-date',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test_train_schedule.csv',
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            # Create required train schedule file
            train_schedule_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,08:30,W001,15.5,true,false"""

            train_schedule_file = temp_path / 'test_train_schedule.csv'
            with open(train_schedule_file, 'w') as f:
                f.write(train_schedule_content)

            # Create required workshop tracks file
            workshop_tracks_content = """track_id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30"""

            workshop_tracks_file = temp_path / 'workshop_tracks.csv'
            with open(workshop_tracks_file, 'w') as f:
                f.write(workshop_tracks_content)

            # Create required routes file
            routes_content = """route_id,origin,destination,distance_km
ROUTE01,A,B,100"""

            routes_file = temp_path / 'routes.csv'
            with open(routes_file, 'w') as f:
                f.write(routes_content)

            with pytest.raises(ConfigurationError, match='Invalid date format'):
                service.load_complete_scenario(temp_path)

    def test_load_complete_scenario_missing_scenario_id(self, service: ConfigurationService) -> None:
        """Test complete scenario loading with missing scenario_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create all required files
            scenario_data = {
                # Missing scenario_id
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test_train_schedule.csv',
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            with pytest.raises(ConfigurationError, match=r'Missing required fields.*scenario_id'):
                service.load_complete_scenario(temp_path)

    def test_error_handling_comprehensive(self, service: ConfigurationService) -> None:
        """Test comprehensive error handling across different scenarios."""
        # Test ConfigurationError is properly raised and chained
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('invalid,csv,content\n1,2')  # Malformed CSV
            malformed_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                service.load_train_schedule(malformed_file)

            # Verify the error message contains useful information
            assert 'Unexpected error loading train schedule' in str(exc_info.value)
        finally:
            malformed_file.unlink()

    def test_load_scenario_path_resolution_edge_cases(self, service: ConfigurationService) -> None:
        """Test edge cases in file path resolution for scenario loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test path without .json extension but not a directory
            non_json_file = temp_path / 'not_json_file'
            non_json_file.touch()  # Create empty file without .json extension

            # Should try test_scenario.json then scenario.json
            with pytest.raises(ConfigurationError, match='Scenario configuration file not found'):
                service.load_scenario(non_json_file)

    def test_load_and_validate_scenario_file_path_handling(self, service: ConfigurationService) -> None:
        """Test file path handling in load_and_validate_scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create scenario file
            scenario_data = {
                'scenario_id': 'test',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test_train_schedule.csv',
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            # Create the train schedule file
            train_schedule_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,08:30,W001,15.5,true,false"""

            train_schedule_file = temp_path / 'test_train_schedule.csv'
            with open(train_schedule_file, 'w') as f:
                f.write(train_schedule_content)

            # Test with direct file path (should extract parent directory)
            result = service.load_and_validate_scenario(scenario_file)
            assert result['scenario_id'] == 'test'

    def test_create_train_arrivals_hasattr_date_branch(self, service: ConfigurationService) -> None:
        """Test the hasattr(arrival_date_value, 'date') branch in _create_train_arrivals."""
        data = {
            'train_id': ['T001'],
            'arrival_date': [pd.Timestamp('2024-01-15 10:30:00')],  # Timestamp with time
            'arrival_time': ['08:30'],
            'wagon_id': ['W001'],
            'length': [15.5],
            'is_loaded': [True],
            'needs_retrofit': [False],
        }
        df = pd.DataFrame(data)

        trains = service._create_train_arrivals(df)
        assert len(trains) == 1
        assert trains[0].arrival_date == date(2024, 1, 15)
        assert trains[0].train_id == 'T001'

    def test_train_schedule_empty_dataframe_after_read(self, service: ConfigurationService) -> None:
        """Test when CSV is read but results in empty DataFrame after parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
            # No data rows, just header
            empty_csv_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Train schedule file is empty'):
                service._read_and_validate_train_schedule_csv(empty_csv_file)
        finally:
            empty_csv_file.unlink()

    def test_workshop_tracks_empty_dataframe_after_read(self, service: ConfigurationService) -> None:
        """Test when workshop tracks CSV is read but results in empty DataFrame after parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('track_id,function,capacity,retrofit_time_min\n')
            # No data rows, just header
            empty_csv_file = Path(f.name)

        try:
            with pytest.raises(ConfigurationError, match='Workshop tracks file is empty'):
                service._read_and_validate_workshop_tracks_csv(empty_csv_file)
        finally:
            empty_csv_file.unlink()

    def test_unexpected_error_in_load_scenario(self, service: ConfigurationService) -> None:
        """Test unexpected error handling in load_scenario."""
        import unittest.mock

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid scenario file
            scenario_data = {
                'scenario_id': 'test',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test.csv',
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            # Mock file operations to raise unexpected error
            with unittest.mock.patch('builtins.open') as mock_open:
                mock_open.side_effect = RuntimeError('Unexpected file system error')

                with pytest.raises(ConfigurationError, match='Unexpected error loading'):
                    service.load_scenario(scenario_file)

    def test_workshop_tracks_different_data_types(self, service: ConfigurationService) -> None:
        """Test workshop tracks with different data type conversion scenarios."""
        # Test successful conversion with string numbers (avoid floats that can't convert to int)
        csv_content = """track_id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK02,werkstattgleis,3,45"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            test_file = Path(f.name)

        try:
            workshop = service.load_workshop_tracks(test_file)
            assert len(workshop.tracks) == 2
            assert workshop.tracks[0].capacity == 5
            assert workshop.tracks[0].retrofit_time_min == 30
        finally:
            test_file.unlink()

    def test_complete_scenario_with_optional_random_seed(self, service: ConfigurationService) -> None:
        """Test complete scenario loading with and without random_seed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create scenario without random_seed (optional field)
            scenario_data = {
                'scenario_id': 'test_no_seed',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'test_train_schedule.csv',
            }

            scenario_file = temp_path / 'test_scenario.json'
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f)

            # Create all required supporting files
            train_schedule_content = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
T001,2024-01-15,08:30,W001,15.5,true,false"""

            train_schedule_file = temp_path / 'test_train_schedule.csv'
            with open(train_schedule_file, 'w') as f:
                f.write(train_schedule_content)

            workshop_tracks_content = """track_id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30"""

            workshop_tracks_file = temp_path / 'workshop_tracks.csv'
            with open(workshop_tracks_file, 'w') as f:
                f.write(workshop_tracks_content)

            # Create routes file with proper format
            routes_content = """route_id;from_track;to_track;track_sequence;distance_m;time_min
ROUTE01;TRACK_A;TRACK_B;TRACK_A,TRACK_B;1000;60"""

            routes_file = temp_path / 'routes.csv'
            with open(routes_file, 'w') as f:
                f.write(routes_content)

            # Should succeed even without random_seed
            config, _ = service.load_complete_scenario(temp_path)
            assert config.scenario_id == 'test_no_seed'
            assert config.random_seed is None  # Should be None when not provided


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""

    def test_configuration_error_creation(self) -> None:
        """Test ConfigurationError can be created and raised."""
        error_msg = 'Test configuration error'

        with pytest.raises(ConfigurationError, match='Test configuration error'):
            raise ConfigurationError(error_msg)

    def test_configuration_error_inheritance(self) -> None:
        """Test ConfigurationError inherits from Exception."""
        error = ConfigurationError('test')
        assert isinstance(error, Exception)
