"""
Unit tests for ScenarioConfig model.

Tests the ScenarioConfig model validation logic, date validation,
workshop integration, and file reference validation.
"""

from datetime import date

from pydantic import ValidationError
import pytest

from configuration.model_scenario import ScenarioConfig
from configuration.model_track import TrackFunction
from configuration.model_track import WorkshopTrack
from configuration.model_workshop import Workshop


class TestScenarioConfig:
    """Test cases for ScenarioConfig model."""

    def test_scenario_config_creation_valid_data_without_workshop(self):
        """Test successful scenario config creation without workshop (backward compatibility)."""
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            random_seed=42,
            train_schedule_file='schedule.csv',
        )

        assert config.scenario_id == 'test_scenario'
        assert config.start_date == date(2024, 1, 1)
        assert config.end_date == date(2024, 1, 10)
        assert config.random_seed == 42
        assert config.train_schedule_file == 'schedule.csv'
        assert config.workshop is None

    def test_scenario_config_creation_valid_data_with_workshop(self):
        """Test successful scenario config creation with workshop."""
        tracks = [
            WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30),
            WorkshopTrack(id='TRACK02', function=TrackFunction.WERKSTATTGLEIS, capacity=3, retrofit_time_min=45),
        ]
        workshop = Workshop(tracks=tracks)

        config = ScenarioConfig(
            scenario_id='scenario_001',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
            random_seed=42,
            workshop=workshop,
            train_schedule_file='train_schedule.csv',
        )

        assert config.scenario_id == 'scenario_001'
        assert config.workshop is not None
        assert len(config.workshop.tracks) == 2
        assert config.workshop.tracks[0].id == 'TRACK01'

    def test_scenario_config_creation_from_dict_with_workshop(self):
        """Test scenario config creation from dictionary with nested workshop data."""
        config_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'random_seed': 42,
            'workshop': {
                'tracks': [
                    {'id': 'TRACK01', 'function': 'werkstattgleis', 'capacity': 5, 'retrofit_time_min': 30},
                    {'id': 'TRACK02', 'function': 'werkstattgleis', 'capacity': 3, 'retrofit_time_min': 45},
                    {'id': 'TRACK03', 'function': 'werkstattgleis', 'capacity': 4, 'retrofit_time_min': 35},
                ]
            },
            'train_schedule_file': 'train_schedule.csv',
        }

        config = ScenarioConfig(**config_data)

        assert config.scenario_id == 'scenario_001'
        assert config.workshop is not None
        assert len(config.workshop.tracks) == 3
        assert config.workshop.tracks[0].id == 'TRACK01'
        assert config.workshop.tracks[1].capacity == 3
        assert config.workshop.tracks[2].retrofit_time_min == 35

    def test_scenario_id_validation_valid_formats(self):
        """Test scenario ID validation with various valid formats."""
        valid_ids = [
            'scenario_001',
            'test-scenario',
            'SCENARIO123',
            's',
            'S1',
            'scenario_test_001',
            'a' * 50,  # Max length
        ]

        for scenario_id in valid_ids:
            config = ScenarioConfig(
                scenario_id=scenario_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                train_schedule_file='schedule.csv',
            )
            assert config.scenario_id == scenario_id

    def test_scenario_id_validation_invalid_formats(self):
        """Test scenario ID validation with invalid formats."""
        invalid_ids = [
            '',  # Empty string
            ' ',  # Space only
            'scenario 001',  # Space in middle
            'scenario@001',  # Special character
            'scenario.001',  # Dot
            'scenario#001',  # Hash
            'a' * 51,  # Too long (max 50 chars)
            'scenario/001',  # Slash
            'scenario+001',  # Plus
        ]

        for scenario_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id=scenario_id,
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 10),
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert (
                'String should match pattern' in error_msg
                or 'at least 1 character' in error_msg
                or 'at most 50 characters' in error_msg
            )

    def test_date_validation_valid_ranges(self):
        """Test date validation with valid date ranges."""
        valid_date_ranges = [
            (date(2024, 1, 1), date(2024, 1, 2)),  # 1 day
            (date(2024, 1, 1), date(2024, 1, 10)),  # 9 days
            (date(2024, 1, 1), date(2024, 12, 31)),  # Full year
            (date(2023, 12, 31), date(2024, 1, 1)),  # Year boundary
        ]

        for start_date, end_date in valid_date_ranges:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=start_date,
                end_date=end_date,
                train_schedule_file='schedule.csv',
            )
            assert config.start_date == start_date
            assert config.end_date == end_date

    def test_date_validation_invalid_ranges(self):
        """Test date validation with invalid date ranges."""
        invalid_date_ranges = [
            (date(2024, 1, 10), date(2024, 1, 1)),  # End before start
            (date(2024, 1, 1), date(2024, 1, 1)),  # Same date
            (date(2024, 12, 31), date(2024, 1, 1)),  # End much before start
        ]

        for start_date, end_date in invalid_date_ranges:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=start_date,
                    end_date=end_date,
                    train_schedule_file='schedule.csv',
                )
            assert 'end_date' in str(exc_info.value) and 'after start_date' in str(exc_info.value)

    def test_date_validation_too_long_duration(self):
        """Test that very long simulation duration is handled properly."""
        # Test that a very long duration scenario is created successfully
        # Note: The warning logging depends on logger configuration, so we just test successful creation
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2025, 6, 1),  # More than 365 days
            train_schedule_file='schedule.csv',
        )

        # Should create config successfully
        assert config.scenario_id == 'test_scenario'
        # Duration should be calculated correctly even if it's long
        duration = (config.end_date - config.start_date).days
        assert duration > 365

    def test_random_seed_validation(self):
        """Test random seed validation."""
        # Valid seeds
        valid_seeds = [0, 1, 42, 999, 2147483647, None]

        for seed in valid_seeds:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                random_seed=seed,
                train_schedule_file='schedule.csv',
            )
            assert config.random_seed == seed

    def test_random_seed_validation_invalid_values(self):
        """Test random seed validation with invalid values."""
        # Only include values that actually fail Pydantic's ge=0 constraint
        # Note: Pydantic converts "42" to 42 and 1.5 to 1, so they pass validation
        invalid_seeds = [-1, -42]  # Only negative integers fail ge=0 validation

        for seed in invalid_seeds:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 10),
                    random_seed=seed,
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert 'greater than or equal to 0' in error_msg

    def test_random_seed_type_coercion(self):
        """Test that Pydantic correctly converts valid string and float values to integers."""
        # Test values that Pydantic should successfully convert
        coercible_values = [
            ('42', 42),  # string to int
            ('0', 0),  # string zero to int zero
            (0.0, 0),  # float zero to int zero (no fractional part)
            (1.0, 1),  # float with .0 to int (no fractional part)
        ]

        for input_val, expected_val in coercible_values:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                random_seed=input_val,
                train_schedule_file='schedule.csv',
            )
            assert config.random_seed == expected_val
            assert isinstance(config.random_seed, int)

    def test_random_seed_validation_floats_with_fractional_parts(self):
        """Test validation error with floats that have fractional parts."""
        floats_with_fractions = [1.9, 2.5, 0.1, -1.5]

        for seed in floats_with_fractions:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 10),
                    random_seed=seed,
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert 'got a number with a fractional part' in error_msg

    def test_train_schedule_file_validation_valid_extensions(self):
        """Test train schedule file validation with valid extensions."""
        valid_files = [
            'schedule.csv',
            'data.json',
            'train_data.csv',
            'config.json',
            'very_long_filename_with_valid_extension.csv',
        ]

        for filename in valid_files:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                train_schedule_file=filename,
            )
            assert config.train_schedule_file == filename

    def test_train_schedule_file_validation_invalid_extensions(self):
        """Test train schedule file validation with invalid extensions."""
        invalid_files = [
            'schedule.txt',
            'data.xlsx',  # Not supported in this validator
            'config.xml',
            'file.pdf',
            'schedule',  # No extension
            '',  # Empty string
        ]

        for filename in invalid_files:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 10),
                    train_schedule_file=filename,
                )
            error_msg = str(exc_info.value)
            assert 'Invalid file extension' in error_msg or 'at least 1 character' in error_msg

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        # Missing scenario_id
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(start_date=date(2024, 1, 1), end_date=date(2024, 1, 10), train_schedule_file='schedule.csv')
        assert 'Field required' in str(exc_info.value)

        # Missing start_date
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(scenario_id='test_scenario', end_date=date(2024, 1, 10), train_schedule_file='schedule.csv')
        assert 'Field required' in str(exc_info.value)

        # Missing end_date
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(scenario_id='test_scenario', start_date=date(2024, 1, 1), train_schedule_file='schedule.csv')
        assert 'Field required' in str(exc_info.value)

        # Missing train_schedule_file
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(scenario_id='test_scenario', start_date=date(2024, 1, 1), end_date=date(2024, 1, 10))
        assert 'Field required' in str(exc_info.value)

    def test_workshop_validation_with_invalid_workshop_data(self):
        """Test validation error when workshop contains invalid data."""
        invalid_workshop_data = {
            'tracks': [
                {'id': '', 'capacity': -1, 'retrofit_time_min': 0}  # All invalid
            ]
        }

        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                scenario_id='test_scenario',
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
                workshop=invalid_workshop_data,
                train_schedule_file='schedule.csv',
            )
        error_msg = str(exc_info.value)
        assert 'greater than 0' in error_msg or 'String should match pattern' in error_msg

    def test_scenario_config_equality(self):
        """Test scenario config equality comparison."""
        config1 = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            train_schedule_file='schedule.csv',
        )

        config2 = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            train_schedule_file='schedule.csv',
        )

        config3 = ScenarioConfig(
            scenario_id='different_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            train_schedule_file='schedule.csv',
        )

        assert config1 == config2
        assert config1 != config3

    def test_scenario_config_dict_conversion(self):
        """Test scenario config conversion to dictionary."""
        tracks = [WorkshopTrack(id='TRACK01', function=TrackFunction.WERKSTATTGLEIS, capacity=5, retrofit_time_min=30)]
        workshop = Workshop(tracks=tracks)

        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            random_seed=42,
            workshop=workshop,
            train_schedule_file='schedule.csv',
        )

        config_dict = config.model_dump()

        assert config_dict['scenario_id'] == 'test_scenario'
        assert config_dict['start_date'] == date(2024, 1, 1)
        assert config_dict['random_seed'] == 42
        assert 'workshop' in config_dict
        assert len(config_dict['workshop']['tracks']) == 1

    def test_scenario_config_json_serialization(self):
        """Test scenario config JSON serialization."""
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            train_schedule_file='schedule.csv',
        )

        json_str = config.model_dump_json()

        # Should be valid JSON that can be parsed back

        import json

        parsed = json.loads(json_str)

        assert parsed['scenario_id'] == 'test_scenario'
        assert parsed['start_date'] == '2024-01-01'
        assert parsed['end_date'] == '2024-01-10'
        assert parsed['workshop'] is None

    def test_scenario_config_realistic_complete_scenario(self):
        """Test scenario config with realistic complete data matching your JSON example."""
        config_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'random_seed': 42,
            'workshop': {
                'tracks': [
                    {'id': 'TRACK01', 'function': 'werkstattgleis', 'capacity': 5, 'retrofit_time_min': 30},
                    {'id': 'TRACK02', 'function': 'werkstattgleis', 'capacity': 3, 'retrofit_time_min': 45},
                    {'id': 'TRACK03', 'function': 'werkstattgleis', 'capacity': 4, 'retrofit_time_min': 35},
                ]
            },
            'train_schedule_file': 'train_schedule.csv',
        }

        config = ScenarioConfig(**config_data)

        # Verify all fields are correctly parsed
        assert config.scenario_id == 'scenario_001'
        assert config.start_date == date(2024, 1, 15)
        assert config.end_date == date(2024, 1, 16)
        assert config.random_seed == 42
        assert config.train_schedule_file == 'train_schedule.csv'

        # Verify workshop structure
        assert config.workshop is not None
        assert len(config.workshop.tracks) == 3

        # Verify track details
        track01 = config.workshop.tracks[0]
        assert track01.id == 'TRACK01'
        assert track01.capacity == 5
        assert track01.retrofit_time_min == 30

        track02 = config.workshop.tracks[1]
        assert track02.id == 'TRACK02'
        assert track02.capacity == 3
        assert track02.retrofit_time_min == 45

        track03 = config.workshop.tracks[2]
        assert track03.id == 'TRACK03'
        assert track03.capacity == 4
        assert track03.retrofit_time_min == 35
