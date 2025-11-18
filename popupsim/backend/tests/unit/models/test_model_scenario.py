"""
Unit tests for Scenario model.

Tests the Scenario model validation logic, date validation,
workshop integration, and file reference validation.
"""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import Any

from models.scenario import Scenario
from pydantic import ValidationError
import pytest


@pytest.fixture
def test_scenario_json_path() -> Path:
    """Return a scenario file path to be loaded."""
    temp_file = Path(tempfile.mkstemp(suffix='.json')[1])
    scenario_data = {
        'scenario_id': 'Test_Scenario',
        'description': 'DAC restrofit simualation',
        'version': '1.0.0',
        'start_date': '2024-01-15',
        'end_date': '2024-01-16',
    }
    temp_file.write_text(json.dumps(scenario_data))
    return temp_file


class TestScenario:
    """Test cases for Scenario model."""

    def test_scenario_config_with_file_from_fixture(self, test_scenario_json_path: Path) -> None:
        """
        Test loading scenario config from a fixture JSON file.

        Parameters
        ----------
        test_scenario_json_path : Path
            Path to the test scenario JSON fixture file.

        Notes
        -----
        Validates that a Scenario can be loaded from a JSON file
        and that all fields match expected values, including date components.
        """
        with open(test_scenario_json_path, encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)

        scenario: Scenario = Scenario(**data)

        assert scenario.scenario_id == 'Test_Scenario'
        # Compare date components (year, month, day) ignoring time
        expected_start = datetime(2024, 1, 15, tzinfo=UTC)
        expected_end = datetime(2024, 1, 16, tzinfo=UTC)
        assert scenario.start_date.date() == expected_start.date()
        assert scenario.end_date.date() == expected_end.date()
        assert scenario.random_seed == 0

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
            config = Scenario(
                scenario_id=scenario_id,
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
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
                Scenario(
                    scenario_id=scenario_id,
                    start_date=datetime(2024, 1, 1, tzinfo=UTC),
                    end_date=datetime(2024, 1, 10, tzinfo=UTC),
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
            config = Scenario(
                scenario_id='test_scenario',
                start_date=start_date,
                end_date=end_date,
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
                Scenario(
                    scenario_id='test_scenario',
                    start_date=start_date,
                    end_date=end_date,
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
        config = Scenario(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 6, 1, tzinfo=UTC),  # More than 365 days
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
            config = Scenario(
                scenario_id='test_scenario',
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 10, tzinfo=UTC),
                random_seed=seed,
            )
            assert config.random_seed == seed

        config = Scenario(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
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
                Scenario(
                    scenario_id='test_scenario',
                    start_date=datetime(2024, 1, 1, tzinfo=UTC),
                    end_date=datetime(2024, 1, 10, tzinfo=UTC),
                    random_seed=seed,
                )
            error_msg = str(exc_info.value)
            assert 'random_seed must be non-negative' in error_msg

    def test_scenario_config_equality(self) -> None:
        """
        Test scenario config equality comparison.

        Notes
        -----
        Validates that Scenario instances with identical field values
        are considered equal, while instances with different values are not.
        """
        config1 = Scenario(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
        )

        config2 = Scenario(
            scenario_id='test_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
        )

        config3 = Scenario(
            scenario_id='different_scenario',
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
        )

        assert config1 == config2
        assert config1 != config3

    def test_scenario_config_json_serialization(self) -> None:
        """
        Test scenario config JSON serialization.

        Notes
        -----
        Validates that Scenario can be serialized to JSON and that
        the resulting JSON string contains expected field values.
        """
        start_date = '2024-01-01 08:00+00:00'
        end_date = '2024-01-10 20:00+00:00'
        config = Scenario(
            scenario_id='test_scenario',
            start_date=start_date,
            end_date=end_date,
        )

        json_str = config.model_dump_json()

        # Should be valid JSON that can be parsed back
        parsed = json.loads(json_str)

        assert parsed['scenario_id'] == 'test_scenario'
        # Verify date fields in parsed JSON match original date values
        assert str(parsed['start_date']).startswith(start_date.split(' ')[0])
        assert str(parsed['end_date']).startswith(end_date.split(' ')[0])
        assert str(parsed['start_date']).startswith(str(datetime(2024, 1, 1, tzinfo=UTC)).split(' ')[0])
        assert str(parsed['end_date']).startswith(str(datetime(2024, 1, 10, tzinfo=UTC)).split(' ')[0])
        assert datetime.fromisoformat(parsed.get('start_date')) == datetime.fromisoformat(start_date)

    def test_scenario_config_realistic_complete_scenario(self) -> None:
        """
        Test scenario config with realistic complete data.

        Notes
        -----
        Validates that Scenario can be created from a dictionary
        matching the structure of actual scenario JSON files, with all
        fields correctly parsed and assigned.
        """
        scenario_data = {
            'scenario_id': 'scenario_001',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'random_seed': 42,
        }

        scenario = Scenario(**scenario_data)

        # Verify all fields are correctly parsed
        assert scenario.scenario_id == 'scenario_001'
        assert scenario.start_date.date() == datetime(2024, 1, 15, tzinfo=UTC).date()
        assert scenario.end_date.date() == datetime(2024, 1, 16, tzinfo=UTC).date()
        assert scenario.random_seed == 42
