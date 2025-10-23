import json
from pathlib import Path

import pandas as pd
import pytest

from configuration.model_scenario import ScenarioConfig
from configuration.model_track import TrackFunction, WorkshopTrackConfig
from configuration.model_train import TrainArrival
from configuration.service import ConfigurationError, ConfigurationService


class TestConfigurationService:
    """Test cases for ConfigurationService class."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create ConfigurationService instance with temporary base path."""
        return ConfigurationService(base_path=tmp_path)

    @pytest.fixture
    def fixtures_path(self):
        """Path to test fixtures directory."""
        return Path(__file__).parent.parent / 'fixtures' / 'config'

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

    @pytest.fixture
    def valid_workshop_tracks_csv(self):
        """Valid CSV data for workshop tracks."""
        return """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK02,werkstattgleis,3,45
TRACK03,sammelgleis,10,0"""

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
            service._read_and_validate_train_schedule_csv(schedule_file)
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
        assert 'Validation failed' in str(exc_info.value)

    def test_read_and_validate_csv_not_dataframe(self, service, tmp_path, monkeypatch):
        """Test ConfigurationError if pandas.read_csv does not return a DataFrame."""

        dummy_csv = tmp_path / 'schedule.csv'
        dummy_csv.write_text('train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')
        # Use monkeypatch to replace pd.read_csv with a function returning None
        monkeypatch.setattr(pd, 'read_csv', lambda *_args, **_kwargs: None)
        with pytest.raises(ConfigurationError) as exc_info:
            service._read_and_validate_train_schedule_csv(dummy_csv)
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
        monkeypatch.setattr(pd, 'read_csv', lambda *_args, **_kwargs: df_mock)
        result = service._read_and_validate_train_schedule_csv(dummy_csv)
        assert isinstance(result, pd.DataFrame)
        assert result.equals(df_mock)

    def test_load_fixture_scenario_success(self, fixtures_path):
        """Test successful loading of fixture scenario configuration."""
        service = ConfigurationService(base_path=fixtures_path)

        config = service.load_scenario(fixtures_path / 'test_scenario.json')

        # Verify basic scenario properties
        assert isinstance(config, ScenarioConfig)
        assert config.scenario_id == 'scenario_001'
        assert config.start_date.strftime('%Y-%m-%d') == '2024-01-15'
        assert config.end_date.strftime('%Y-%m-%d') == '2024-01-16'
        assert config.random_seed == 42
        assert config.train_schedule_file == 'train_schedule.csv'

        # Verify workshop configuration
        assert config.workshop is not None
        assert len(config.workshop.tracks) == 3

        # Verify individual tracks
        track1 = config.workshop.tracks[0]
        assert track1.id == 'TRACK01'
        assert track1.capacity == 5
        assert track1.retrofit_time_min == 30

        track2 = config.workshop.tracks[1]
        assert track2.id == 'TRACK02'
        assert track2.capacity == 3
        assert track2.retrofit_time_min == 45

        track3 = config.workshop.tracks[2]
        assert track3.id == 'TRACK03'
        assert track3.capacity == 4
        assert track3.retrofit_time_min == 35

    def test_load_fixture_train_schedule_success(self, fixtures_path):
        """Test successful loading of fixture train schedule."""
        service = ConfigurationService(base_path=fixtures_path)

        trains = service.load_train_schedule(fixtures_path / 'test_train_schedule.csv')

        assert len(trains) == 3

        train1 = next(t for t in trains if t.train_id == 'TRAIN001')
        assert train1.arrival_date.strftime('%Y-%m-%d') == '2024-01-15'
        assert train1.arrival_time.strftime('%H:%M') == '08:00'
        assert len(train1.wagons) == 3

        wagon_ids = [w.wagon_id for w in train1.wagons]
        assert 'WAGON001_01' in wagon_ids
        assert 'WAGON001_02' in wagon_ids
        assert 'WAGON001_03' in wagon_ids

        train2 = next(t for t in trains if t.train_id == 'TRAIN002')
        assert train2.arrival_time.strftime('%H:%M') == '10:30'
        assert len(train2.wagons) == 2

        train3 = next(t for t in trains if t.train_id == 'TRAIN003')
        assert train3.arrival_time.strftime('%H:%M') == '14:15'
        assert len(train3.wagons) == 3

    def test_load_fixture_complete_scenario_success(self, fixtures_path):
        """Test successful loading of complete fixture scenario with train schedule."""
        service = ConfigurationService(base_path=fixtures_path)

        config, trains = service.load_complete_scenario(fixtures_path / 'test_scenario.json')

        assert isinstance(config, ScenarioConfig)
        assert config.scenario_id == 'scenario_001'
        assert config.workshop is not None
        assert len(config.workshop.tracks) == 3

        assert len(trains) == 3
        train_ids = [t.train_id for t in trains]
        assert 'TRAIN001' in train_ids
        assert 'TRAIN002' in train_ids
        assert 'TRAIN003' in train_ids

        # Verify all trains arrive within scenario date range
        for train in trains:
            assert config.start_date <= train.arrival_date <= config.end_date

    def test_load_fixture_scenario_corrupted_json(self, fixtures_path, tmp_path):
        """Test ConfigurationError with corrupted JSON fixture."""
        service = ConfigurationService(base_path=fixtures_path)

        # Create corrupted JSON file
        corrupted_file = tmp_path / 'corrupted_scenario.json'
        corrupted_file.write_text('{"scenario_id": "test", "invalid": json syntax}')

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(corrupted_file)
        assert 'Invalid JSON syntax' in str(exc_info.value)

    def test_load_fixture_scenario_missing_workshop_tracks(self, tmp_path):
        """Test ConfigurationError with scenario missing workshop tracks."""
        service = ConfigurationService(base_path=tmp_path)

        # Create scenario with empty workshop tracks
        invalid_scenario = {
            'scenario_id': 'test_scenario',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'workshop': {
                'tracks': []  # Invalid: empty tracks
            },
            'train_schedule_file': 'test_train_schedule.csv',
        }

        scenario_file = tmp_path / 'invalid_scenario.json'
        scenario_file.write_text(json.dumps(invalid_scenario))

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(scenario_file)
        assert 'at least 1 item' in str(exc_info.value)

    def test_load_fixture_scenario_duplicate_track_ids(self, tmp_path):
        """Test ConfigurationError with duplicate track IDs in workshop."""
        service = ConfigurationService(base_path=tmp_path)

        # Create scenario with duplicate track IDs
        invalid_scenario = {
            'scenario_id': 'test_scenario',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'workshop': {
                'tracks': [
                    {'id': 'TRACK01', 'function': 'werkstattgleis', 'capacity': 5, 'retrofit_time_min': 30},
                    {
                        'id': 'TRACK01',
                        'function': 'werkstattgleis',
                        'capacity': 3,
                        'retrofit_time_min': 45,
                    },  # Duplicate ID
                ]
            },
            'train_schedule_file': 'test_train_schedule.csv',
        }

        scenario_file = tmp_path / 'duplicate_tracks_scenario.json'
        scenario_file.write_text(json.dumps(invalid_scenario))

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_scenario(scenario_file)
        assert 'Duplicate track IDs found' in str(exc_info.value)

    def test_load_fixture_train_schedule_missing_columns(self, tmp_path):
        """Test ConfigurationError with train schedule missing required columns."""
        service = ConfigurationService(base_path=tmp_path)

        # Create CSV with missing columns
        incomplete_csv = """train_id,arrival_date,arrival_time,wagon_id
TRAIN001,2024-01-15,08:00,WAGON001
"""

        schedule_file = tmp_path / 'incomplete_schedule.csv'
        schedule_file.write_text(incomplete_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'Missing required columns' in str(exc_info.value)
        assert 'arrival_date' in str(exc_info.value)
        assert 'arrival_time' in str(exc_info.value)

    def test_load_fixture_train_schedule_invalid_date_format(self, tmp_path):
        """Test ConfigurationError with invalid date format in train schedule."""
        service = ConfigurationService(base_path=tmp_path)

        # Create CSV with invalid date format
        invalid_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,invalid-date,08:00,WAGON001,15.5,true,true
"""

        schedule_file = tmp_path / 'invalid_date_schedule.csv'
        schedule_file.write_text(invalid_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        # The error could be about date parsing or validation
        error_msg = str(exc_info.value)
        assert 'Invalid' in error_msg or 'parse' in error_msg.lower() or 'date' in error_msg.lower()

    def test_load_fixture_train_schedule_invalid_time_format(self, tmp_path):
        """Test ConfigurationError with invalid time format in train schedule."""
        service = ConfigurationService(base_path=tmp_path)

        # Create CSV with invalid time format
        invalid_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,25:99,WAGON001,15.5,true,true
"""

        schedule_file = tmp_path / 'invalid_time_schedule.csv'
        schedule_file.write_text(invalid_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        # The actual error message format from the service
        error_msg = str(exc_info.value)
        assert 'Invalid time format' in error_msg or 'must be in HH:MM format' in error_msg or '25:99' in error_msg

    def test_load_fixture_train_schedule_negative_wagon_length(self, tmp_path):
        """Test ConfigurationError with negative wagon length."""
        service = ConfigurationService(base_path=tmp_path)

        # Create CSV with negative wagon length
        invalid_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,08:00,WAGON001,-15.5,true,true
"""

        schedule_file = tmp_path / 'negative_length_schedule.csv'
        schedule_file.write_text(invalid_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_train_schedule(schedule_file)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_fixture_scenario_trains_outside_date_range(self, tmp_path):
        """Test ConfigurationError when fixture trains arrive outside modified scenario date range."""
        service = ConfigurationService(base_path=tmp_path)

        # Create scenario with date range that excludes fixture train arrivals
        scenario_data = {
            'scenario_id': 'test_scenario',
            'start_date': '2024-01-01',  # Fixture trains arrive on 2024-01-15
            'end_date': '2024-01-10',  # which is outside this range
            'train_schedule_file': 'test_train_schedule.csv',
        }

        scenario_file = tmp_path / 'narrow_range_scenario.json'
        scenario_file.write_text(json.dumps(scenario_data))

        # Create the train schedule file with trains outside the date range
        out_of_range_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,08:00,WAGON001,15.5,true,false
TRAIN002,2024-01-15,10:00,WAGON002,12.0,false,true
"""
        schedule_file = tmp_path / 'test_train_schedule.csv'
        schedule_file.write_text(out_of_range_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_complete_scenario(scenario_file)
        assert 'outside scenario date range' in str(exc_info.value)

    def test_load_fixture_scenario_with_workshop_validation_success(self, fixtures_path):
        """Test that loading fixture scenario with workshop validates successfully."""
        service = ConfigurationService(base_path=fixtures_path)

        # Load and validate complete scenario
        config = service.load_and_validate_scenario(fixtures_path / 'test_scenario.json')

        assert config.workshop is not None
        assert len(config.workshop.tracks) == 3

        # Verify no duplicate track IDs
        track_ids = [track.id for track in config.workshop.tracks]
        assert len(track_ids) == len(set(track_ids))

        # Verify all tracks have valid properties
        for track in config.workshop.tracks:
            assert track.capacity > 0
            assert track.retrofit_time_min > 0
            assert len(track.id) > 0

    def test_load_fixture_train_schedule_with_boolean_variations(self, tmp_path):
        """Test successful loading with various boolean format variations."""
        service = ConfigurationService(base_path=tmp_path)

        # Create CSV with different boolean representations
        varied_csv = """train_id,arrival_date,arrival_time,wagon_id,length,is_loaded,needs_retrofit
TRAIN001,2024-01-15,08:00,WAGON001,15.5,true,false
TRAIN002,2024-01-15,10:00,WAGON002,12.0,True,False
TRAIN003,2024-01-15,12:00,WAGON003,18.0,1,0
TRAIN004,2024-01-15,14:00,WAGON004,20.0,yes,no
"""

        schedule_file = tmp_path / 'boolean_variations_schedule.csv'
        schedule_file.write_text(varied_csv)

        trains = service.load_train_schedule(schedule_file)

        # Verify all trains loaded successfully with correct boolean values
        assert len(trains) == 4

        # Check boolean parsing worked correctly
        train1 = next(t for t in trains if t.train_id == 'TRAIN001')
        assert train1.wagons[0].is_loaded is True
        assert train1.wagons[0].needs_retrofit is False

    def test_load_workshop_tracks_success(self, service, tmp_path, valid_workshop_tracks_csv):
        """Test successful loading of workshop tracks from CSV file."""
        tracks_file = tmp_path / 'workshop_tracks.csv'
        tracks_file.write_text(valid_workshop_tracks_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 3
        assert isinstance(tracks[0], WorkshopTrackConfig)

        # Verify first track
        track1 = tracks[0]
        assert track1.id == 'TRACK01'
        assert track1.function == TrackFunction.WERKSTATTGLEIS
        assert track1.capacity == 5
        assert track1.retrofit_time_min == 30

        # Verify second track
        track2 = tracks[1]
        assert track2.id == 'TRACK02'
        assert track2.function == TrackFunction.WERKSTATTGLEIS
        assert track2.capacity == 3
        assert track2.retrofit_time_min == 45

        # Verify third track (sammelgleis)
        track3 = tracks[2]
        assert track3.id == 'TRACK03'
        assert track3.function == TrackFunction.SAMMELGLEIS
        assert track3.capacity == 10
        assert track3.retrofit_time_min == 0

    def test_load_workshop_tracks_file_not_found(self, service, tmp_path):
        """Test ConfigurationError when workshop tracks file not found."""
        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tmp_path / 'nonexistent_tracks.csv')
        assert 'Workshop tracks file not found' in str(exc_info.value)

    def test_load_workshop_tracks_empty_file(self, service, tmp_path):
        """Test ConfigurationError for empty workshop tracks CSV file."""
        tracks_file = tmp_path / 'empty_tracks.csv'
        tracks_file.write_text('')

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'No columns to parse from file' in str(exc_info.value) or 'Workshop tracks file is empty' in str(
            exc_info.value
        )

    def test_load_workshop_tracks_missing_required_columns(self, service, tmp_path):
        """Test ConfigurationError for missing required columns in workshop tracks CSV."""
        incomplete_csv = """id,function
TRACK01,werkstattgleis"""

        tracks_file = tmp_path / 'incomplete_tracks.csv'
        tracks_file.write_text(incomplete_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Missing required columns' in str(exc_info.value)
        assert 'capacity' in str(exc_info.value)
        assert 'retrofit_time_min' in str(exc_info.value)

    def test_load_workshop_tracks_duplicate_track_ids(self, service, tmp_path):
        """Test ConfigurationError for duplicate track IDs in workshop tracks."""
        duplicate_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK01,werkstattgleis,3,45"""

        tracks_file = tmp_path / 'duplicate_tracks.csv'
        tracks_file.write_text(duplicate_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Duplicate track IDs found' in str(exc_info.value)
        assert 'TRACK01' in str(exc_info.value)

    def test_load_workshop_tracks_invalid_capacity_type(self, service, tmp_path):
        """Test ConfigurationError for invalid capacity data type."""
        invalid_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,invalid_capacity,30"""

        tracks_file = tmp_path / 'invalid_capacity_tracks.csv'
        tracks_file.write_text(invalid_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        error_msg = str(exc_info.value)
        assert 'Unexpected error' in error_msg or 'invalid literal for int()' in error_msg

    def test_load_workshop_tracks_invalid_retrofit_time_type(self, service, tmp_path):
        """Test ConfigurationError for invalid retrofit_time_min data type."""
        invalid_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,invalid_time"""

        tracks_file = tmp_path / 'invalid_time_tracks.csv'
        tracks_file.write_text(invalid_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        error_msg = str(exc_info.value)
        assert 'Unexpected error' in error_msg or 'invalid literal for int()' in error_msg

    def test_load_workshop_tracks_negative_capacity(self, service, tmp_path):
        """Test ConfigurationError for negative capacity values."""
        negative_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,-5,30"""

        tracks_file = tmp_path / 'negative_capacity_tracks.csv'
        tracks_file.write_text(negative_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_workshop_tracks_negative_retrofit_time(self, service, tmp_path):
        """Test ConfigurationError for negative retrofit_time_min values."""
        negative_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,-30"""

        tracks_file = tmp_path / 'negative_time_tracks.csv'
        tracks_file.write_text(negative_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_workshop_tracks_empty_track_id(self, service, tmp_path):
        """Test ConfigurationError for empty track ID."""
        empty_id_csv = """id,function,capacity,retrofit_time_min
,werkstattgleis,5,30"""

        tracks_file = tmp_path / 'empty_id_tracks.csv'
        tracks_file.write_text(empty_id_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_workshop_tracks_empty_function(self, service, tmp_path):
        """Test ConfigurationError for empty function field."""
        empty_function_csv = """id,function,capacity,retrofit_time_min
TRACK01,,5,30"""

        tracks_file = tmp_path / 'empty_function_tracks.csv'
        tracks_file.write_text(empty_function_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        error_msg = str(exc_info.value)
        assert 'Invalid data type for track TRACK01' in error_msg

    def test_load_workshop_tracks_zero_capacity(self, service, tmp_path):
        """Test ConfigurationError for zero capacity values."""
        zero_capacity_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,0,30"""

        tracks_file = tmp_path / 'zero_capacity_tracks.csv'
        tracks_file.write_text(zero_capacity_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Validation failed' in str(exc_info.value)

    def test_load_workshop_tracks_malformed_csv(self, service, tmp_path):
        """Test ConfigurationError for malformed CSV structure."""
        malformed_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30,extra_column_value
TRACK02,werkstattgleis"""  # Missing values

        tracks_file = tmp_path / 'malformed_tracks.csv'
        tracks_file.write_text(malformed_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        error_msg = str(exc_info.value)
        assert 'Unexpected error' in error_msg or 'Integer column has NA values' in error_msg

    def test_load_workshop_tracks_extra_columns_ignored(self, service, tmp_path):
        """Test that extra columns in CSV are ignored."""
        extra_columns_csv = """id,function,capacity,retrofit_time_min,extra_column,another_extra
TRACK01,werkstattgleis,5,30,ignored1,ignored2
TRACK02,sammelgleis,8,0,ignored3,ignored4"""

        tracks_file = tmp_path / 'extra_columns_tracks.csv'
        tracks_file.write_text(extra_columns_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 2
        assert tracks[0].id == 'TRACK01'
        assert tracks[0].function == TrackFunction.WERKSTATTGLEIS
        assert tracks[0].capacity == 5
        assert tracks[0].retrofit_time_min == 30

    def test_load_workshop_tracks_whitespace_handling(self, service, tmp_path):
        """Test that whitespace in CSV values is handled correctly."""
        whitespace_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK02,sammelgleis,8,0"""

        tracks_file = tmp_path / 'whitespace_tracks.csv'
        tracks_file.write_text(whitespace_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 2
        # Verify whitespace is properly handled
        assert tracks[0].id == 'TRACK01'  # Should be trimmed
        assert tracks[0].function == TrackFunction.WERKSTATTGLEIS  # Should be trimmed
        assert tracks[0].capacity == 5
        assert tracks[0].retrofit_time_min == 30

    def test_load_workshop_tracks_single_track(self, service, tmp_path):
        """Test successful loading of single workshop track."""
        single_track_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30"""

        tracks_file = tmp_path / 'single_track.csv'
        tracks_file.write_text(single_track_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 1
        assert tracks[0].id == 'TRACK01'
        assert tracks[0].function == TrackFunction.WERKSTATTGLEIS
        assert tracks[0].capacity == 5
        assert tracks[0].retrofit_time_min == 30

    def test_load_workshop_tracks_multiple_functions(self, service, tmp_path):
        """Test loading workshop tracks with multiple function types."""
        multi_function_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK02,sammelgleis,10,0
TRACK03,parkgleis,8,0
TRACK04,werkstattgleis,3,45"""

        tracks_file = tmp_path / 'multi_function_tracks.csv'
        tracks_file.write_text(multi_function_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 4

        # Verify different function types
        functions = [track.function for track in tracks]
        assert TrackFunction.WERKSTATTGLEIS in functions
        assert TrackFunction.SAMMELGLEIS in functions
        assert TrackFunction.PARKGLEIS in functions

        # Verify werkstattgleis tracks have non-zero retrofit times
        werkstatt_tracks = [track for track in tracks if track.function == TrackFunction.WERKSTATTGLEIS]
        for track in werkstatt_tracks:
            assert track.retrofit_time_min > 0

        # Verify non-werkstattgleis tracks have zero retrofit times
        non_werkstatt_tracks = [track for track in tracks if track.function != TrackFunction.WERKSTATTGLEIS]
        for track in non_werkstatt_tracks:
            assert track.retrofit_time_min == 0

    def test_load_workshop_tracks_large_capacity_values(self, service, tmp_path):
        """Test loading workshop tracks with large capacity values."""
        large_capacity_csv = """id,function,capacity,retrofit_time_min
TRACK01,sammelgleis,1000,0
TRACK02,werkstattgleis,500,60"""

        tracks_file = tmp_path / 'large_capacity_tracks.csv'
        tracks_file.write_text(large_capacity_csv)

        workshop = service.load_workshop_tracks(tracks_file)
        tracks = workshop.tracks
        assert len(tracks) == 2
        assert tracks[0].capacity == 1000
        assert tracks[1].capacity == 500

    def test_load_workshop_tracks_pandas_dataframe_validation(self, service, tmp_path, monkeypatch):
        """Test ConfigurationError if pandas.read_csv does not return a DataFrame."""
        tracks_file = tmp_path / 'test_tracks.csv'
        tracks_file.write_text('id,function,capacity,retrofit_time_min\n')

        # Mock pd.read_csv to return None instead of DataFrame
        monkeypatch.setattr(pd, 'read_csv', lambda *_args, **_kwargs: None)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'not a pandas DataFrame' in str(exc_info.value)

    def test_create_workshop_tracks_from_dataframe_success(self, service):
        """Test successful creation of WorkshopTrackConfig objects from DataFrame."""
        df = pd.DataFrame(
            {
                'id': ['TRACK01', 'TRACK02'],
                'function': ['werkstattgleis', 'sammelgleis'],
                'capacity': [5, 10],
                'retrofit_time_min': [30, 0],
            }
        )

        tracks = service._create_workshop_tracks_from_dataframe(df)

        assert len(tracks) == 2
        assert isinstance(tracks[0], WorkshopTrackConfig)
        assert tracks[0].id == 'TRACK01'
        assert tracks[0].function == TrackFunction.WERKSTATTGLEIS
        assert tracks[0].capacity == 5
        assert tracks[0].retrofit_time_min == 30

    def test_create_workshop_tracks_from_dataframe_validation_error(self, service):
        """Test ConfigurationError when WorkshopTrackConfig validation fails."""
        # DataFrame with invalid data (negative capacity)
        df = pd.DataFrame(
            {
                'id': ['TRACK01'],
                'function': ['werkstattgleis'],
                'capacity': [-5],  # Invalid: negative capacity
                'retrofit_time_min': [30],
            }
        )

        with pytest.raises(ConfigurationError) as exc_info:
            service._create_workshop_tracks_from_dataframe(df)
        assert 'Validation failed for track TRACK01' in str(exc_info.value)

    def test_create_workshop_tracks_from_dataframe_type_error(self, service):
        """Test ConfigurationError when DataFrame contains invalid data types."""
        # DataFrame with invalid data types
        df = pd.DataFrame(
            {
                'id': ['TRACK01'],
                'function': ['werkstattgleis'],
                'capacity': ['invalid'],  # Invalid: string instead of int
                'retrofit_time_min': [30],
            }
        )

        with pytest.raises(ConfigurationError) as exc_info:
            service._create_workshop_tracks_from_dataframe(df)
        assert 'Invalid data type for track TRACK01' in str(exc_info.value)

    def test_load_workshop_tracks_invalid_function_enum(self, service, tmp_path):
        """Test ConfigurationError for invalid function enum value."""
        invalid_function_csv = """id,function,capacity,retrofit_time_min
TRACK01,invalid_function,5,30"""

        tracks_file = tmp_path / 'invalid_function_tracks.csv'
        tracks_file.write_text(invalid_function_csv)

        with pytest.raises(ConfigurationError) as exc_info:
            service.load_workshop_tracks(tracks_file)
        assert 'Invalid data type for track TRACK01' in str(exc_info.value)

    def test_load_workshop_tracks_all_valid_functions(self, service, tmp_path):
        """Test loading workshop tracks with all valid function enum values."""
        all_functions_csv = """id,function,capacity,retrofit_time_min
TRACK01,werkstattgleis,5,30
TRACK02,sammelgleis,8,0
TRACK03,parkgleis,6,0
TRACK04,werkstattzufuehrung,4,0
TRACK05,werkstattabfuehrung,3,0
TRACK06,bahnhofskopf,10,0"""

        tracks_file = tmp_path / 'all_functions_tracks.csv'
        tracks_file.write_text(all_functions_csv)

        tracks = service.load_workshop_tracks(tracks_file)
        tracks = tracks.tracks
        assert len(tracks) == 6

        # Verify all function types are present
        functions = [track.function for track in tracks]
        expected_functions = [
            TrackFunction.WERKSTATTGLEIS,
            TrackFunction.SAMMELGLEIS,
            TrackFunction.PARKGLEIS,
            TrackFunction.WERKSTATTZUFUEHRUNG,
            TrackFunction.WERKSTATTABFUEHRUNG,
            TrackFunction.BAHNHOFSKOPF,
        ]
        for expected_func in expected_functions:
            assert expected_func in functions

        # Verify only werkstattgleis has non-zero retrofit time
        for track in tracks:
            if track.function == TrackFunction.WERKSTATTGLEIS:
                assert track.retrofit_time_min > 0
            else:
                assert track.retrofit_time_min == 0
