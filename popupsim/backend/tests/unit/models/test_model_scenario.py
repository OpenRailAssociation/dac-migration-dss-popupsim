"""
Unit tests for ScenarioConfig model.

Tests the ScenarioConfig model validation logic, date validation,
workshop integration, and file reference validation.
"""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from models.scenario import ScenarioConfig
from pydantic import ValidationError
import pytest


class TestScenarioConfig:
    """Test cases for ScenarioConfig model."""

    def test_scenario_config_with_file_from_fixture(self, test_scenario_json_path: Path) -> None:
        """
        Test loading scenario config from a fixture JSON file.

        Parameters
        ----------
        test_scenario_json_path : Path
            Path to the test scenario JSON fixture file.

        Notes
        -----
        Validates that a ScenarioConfig can be loaded from a JSON file
        and that all fields match expected values, including date components.
        """
        with open(test_scenario_json_path, encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)

        scenario: ScenarioConfig = ScenarioConfig(**data)

        assert scenario.scenario_id == 'scenario_001'
        # Compare date components (year, month, day) ignoring time
        expected_start = datetime(2024, 1, 15, tzinfo=UTC)
        expected_end = datetime(2024, 1, 16, tzinfo=UTC)
        assert scenario.start_date.date() == expected_start.date()
        assert scenario.end_date.date() == expected_end.date()
        assert scenario.random_seed == 0
        assert scenario.train_schedule_file == 'test_train_schedule.csv'

    def test_scenario_config_creation_valid_data_without_workshop(self) -> None:
        """
        Test successful scenario config creation without workshop.

        Notes
        -----
        Tests backward compatibility for scenarios without workshop models.
        Validates that all required fields are correctly assigned.
        Date fields can be set from strings and datetime objects.
        """
        scenario = ScenarioConfig(
            scenario_id='test_scenario',
            start_date='2024-01-01',
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            random_seed=42,
            train_schedule_file='schedule.csv',
        )

        assert scenario.scenario_id == 'test_scenario'
        expected_start = datetime(2024, 1, 1, tzinfo=UTC)
        expected_end = datetime(2024, 1, 10, tzinfo=UTC)
        assert scenario.start_date.date() == expected_start.date()
        assert scenario.end_date.date() == expected_end.date()
        assert scenario.random_seed == 42
        assert scenario.train_schedule_file == 'schedule.csv'

    def test_scenario_id_validation_valid_formats(self) -> None:
        """
        Test scenario ID validation with various valid formats.

        Notes
        -----
        Validates that scenario IDs matching the pattern (alphanumeric, underscore,
        hyphen, 1-50 chars) are accepted.
        """
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
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                train_schedule_file='schedule.csv',
            )
            assert config.scenario_id == scenario_id

    def test_scenario_id_validation_invalid_formats(self) -> None:
        """
        Test scenario ID validation with invalid formats.

        Notes
        -----
        Validates that scenario IDs with invalid characters, length, or format
        raise ValidationError.
        """
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
                    start_date=datetime(2024, 1, 1, tzinfo=UTC),
                    end_date=datetime(2024, 1, 10, tzinfo=UTC),
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert (
                'String should match pattern' in error_msg
                or 'at least 1 character' in error_msg
                or 'at most 50 characters' in error_msg
            )

    def test_date_validation_valid_ranges(self) -> None:
        """
        Test date validation with valid date ranges.

        Notes
        -----
        Validates that various valid date ranges (1 day to full year) are accepted
        and correctly stored.
        """
        valid_date_ranges = [
            (datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC)),  # 1 day
            (datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 10, tzinfo=UTC)),  # 9 days
            (datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 12, 31, tzinfo=UTC)),  # Full year
            (datetime(2023, 12, 31, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)),  # Year boundary
        ]

        for start_date, end_date in valid_date_ranges:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=start_date,
                end_date=end_date,
                train_schedule_file='schedule.csv',
            )
            assert config.start_date.date() == start_date.date()
            assert config.end_date.date() == end_date.date()

    def test_date_validation_invalid_ranges(self) -> None:
        """
        Test date validation with invalid date ranges.

        Notes
        -----
        Validates that date ranges where end_date is before or equal to start_date
        raise ValidationError.
        """
        invalid_date_ranges = [
            (datetime(2024, 1, 10, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)),  # End before start
            (datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)),  # Same date
            (datetime(2024, 12, 31, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)),  # End much before start
        ]

        for start_date, end_date in invalid_date_ranges:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=start_date,
                    end_date=end_date,
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert 'end_date' in error_msg
            assert 'after start_date' in error_msg

    def test_date_validation_too_long_duration(self) -> None:
        """
        Test that very long simulation duration is handled properly.

        Notes
        -----
        Validates that scenarios with duration exceeding 365 days are created
        successfully and duration is calculated correctly. Warning logging is
        implementation-dependent and not tested here.
        """
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 6, 1, tzinfo=UTC),  # More than 365 days
            train_schedule_file='schedule.csv',
        )

        # Should create config successfully
        assert config.scenario_id == 'test_scenario'
        # Duration should be calculated correctly even if it's long
        duration = (config.end_date - config.start_date).days
        assert duration > 365

    def test_random_seed_validation(self) -> None:
        """
        Test random seed validation with valid values.

        Notes
        -----
        Validates that non-negative integer seeds are accepted and that
        default value (0) is applied when seed is not specified.
        """
        # Valid seeds
        valid_seeds = [0, 1, 42, 999, 2147483647]

        for seed in valid_seeds:
            config = ScenarioConfig(
                scenario_id='test_scenario',
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                random_seed=seed,
                train_schedule_file='schedule.csv',
            )
            assert config.random_seed == seed

        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            train_schedule_file='schedule.csv',
        )
        assert config.random_seed == 0  # Default value

    def test_random_seed_validation_invalid_values(self) -> None:
        """
        Test random seed validation with invalid values.

        Notes
        -----
        Validates that negative integer seeds raise ValidationError with
        appropriate constraint message (ge=0).
        """
        invalid_seeds = [-1, -42]

        for seed in invalid_seeds:
            with pytest.raises(ValidationError) as exc_info:
                ScenarioConfig(
                    scenario_id='test_scenario',
                    start_date=datetime(2024, 1, 1, tzinfo=UTC),
                    end_date=datetime(2024, 1, 10, tzinfo=UTC),
                    random_seed=seed,
                    train_schedule_file='schedule.csv',
                )
            error_msg = str(exc_info.value)
            assert 'random_seed must be non-negative' in error_msg

    def test_train_schedule_file_validation_valid_extensions(self) -> None:
        """
        Test train schedule file validation with valid extensions.

        Notes
        -----
        Validates that files with .csv or .json extensions are accepted.
        """
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
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                train_schedule_file=filename,
            )
            assert config.train_schedule_file == filename

    def test_train_schedule_file_validation_invalid_extensions(self) -> None:
        """
        Test train schedule file validation with invalid extensions.

        Notes
        -----
        Validates that files with unsupported extensions or missing extensions
        raise ValidationError.
        """
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
                    start_date=datetime(2024, 1, 1, tzinfo=UTC),
                    end_date=datetime(2024, 1, 10, tzinfo=UTC),
                    train_schedule_file=filename,
                )
            error_msg = str(exc_info.value)
            assert 'Invalid file extension' in error_msg or 'at least 1 character' in error_msg

    def test_missing_required_fields(self) -> None:
        """
        Test validation error when required fields are missing.

        Notes
        -----
        Validates that omitting any required field raises ValidationError
        with 'Field required' message.
        """
        # Missing scenario_id
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                train_schedule_file='schedule.csv',
            )
        assert 'Field required' in str(exc_info.value)

        # Missing start_date
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                scenario_id='test_scenario',
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                train_schedule_file='schedule.csv',
            )
        assert 'Field required' in str(exc_info.value)

        # Missing end_date
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                scenario_id='test_scenario',
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                train_schedule_file='schedule.csv',
            )
        assert 'Field required' in str(exc_info.value)

        # Missing train_schedule_file
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                scenario_id='test_scenario',
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
            )
        assert 'Field required' in str(exc_info.value)

    def test_scenario_config_equality(self) -> None:
        """
        Test scenario config equality comparison.

        Notes
        -----
        Validates that ScenarioConfig instances with identical field values
        are considered equal, while instances with different values are not.
        """
        config1 = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            train_schedule_file='schedule.csv',
        )

        config2 = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            train_schedule_file='schedule.csv',
        )

        config3 = ScenarioConfig(
            scenario_id='different_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            train_schedule_file='schedule.csv',
        )

        assert config1 == config2
        assert config1 != config3

    def test_scenario_config_json_serialization(self) -> None:
        """
        Test scenario config JSON serialization.

        Notes
        -----
        Validates that ScenarioConfig can be serialized to JSON and that
        the resulting JSON string contains expected field values.
        """
        start_date = '2024-01-01 08:00+00:00'
        end_date = '2024-01-10 20:00+00:00'
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=start_date,
            end_date=end_date,
            train_schedule_file='schedule.csv',
        )

        json_str = config.model_dump_json()

        # Should be valid JSON that can be parsed back
        parsed = json.loads(json_str)

        assert parsed['scenario_id'] == 'test_scenario'
        # Verify date fields in parsed JSON match original date values
        assert str(parsed['start_date']).startswith((start_date).split(' ')[0])
        assert str(parsed['end_date']).startswith((end_date).split(' ')[0])
        assert str(parsed['start_date']).startswith(str(datetime(2024, 1, 1, tzinfo=UTC)).split(' ')[0])
        assert str(parsed['end_date']).startswith(str(datetime(2024, 1, 10, tzinfo=UTC)).split(' ')[0])
        assert datetime.fromisoformat(parsed.get('start_date')) == datetime.fromisoformat(start_date)

    def test_scenario_config_realistic_complete_scenario(self) -> None:
        """
        Test scenario config with realistic complete data.

        Notes
        -----
        Validates that ScenarioConfig can be created from a dictionary
        matching the structure of actual scenario JSON files, with all
        fields correctly parsed and assigned.
        """
        config_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'random_seed': 42,
            'train_schedule_file': 'train_schedule.csv',
        }

        config = ScenarioConfig(**config_data)

        # Verify all fields are correctly parsed
        assert config.scenario_id == 'scenario_001'
        assert config.start_date.date() == datetime(2024, 1, 15, tzinfo=UTC).date()
        assert config.end_date.date() == datetime(2024, 1, 16, tzinfo=UTC).date()
        assert config.random_seed == 42

    def test_scenario_config_with_file_references(self) -> None:
        """
        Test scenario config with external file references.

        Notes
        -----
        Validates that file references are stored correctly. Actual file
        loading and validation should be tested with service layer tests.
        """
        config = ScenarioConfig(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            train_schedule_file='schedule.csv',
        )

        assert config.train_schedule_file == 'schedule.csv'
