"""Unit tests for Workshop model.

Tests for workshop configuration validation including stations, workers, and dates.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import pytest
from workshop_operations.domain.entities.workshop import Workshop


@pytest.mark.unit
class TestWorkshop:
    """Test suite for Workshop model."""

    def test_workshop_creation_with_all_fields(self) -> None:
        """Test creating workshop with all required fields."""
        workshop: Workshop = Workshop(
            id='WS_TEST_01',
            start_date='2031-07-04T00:00:00',
            end_date='2031-07-25T23:59:59',
            retrofit_stations=2,
            track='track_10',
            worker=4,
        )

        assert workshop.id == 'WS_TEST_01'
        assert workshop.start_date == '2031-07-04T00:00:00'
        assert workshop.end_date == '2031-07-25T23:59:59'
        assert workshop.retrofit_stations == 2
        assert workshop.track == 'track_10'
        assert workshop.worker == 4

    def test_workshop_creation_with_defaults(self) -> None:
        """Test creating workshop with default values."""
        workshop: Workshop = Workshop(
            id='WS_TEST_02',
            start_date='2031-07-04T00:00:00',
            end_date='2031-07-25T23:59:59',
            track='track_Z1',
        )

        assert workshop.id == 'WS_TEST_02'
        assert workshop.retrofit_stations == 1
        assert workshop.worker == 1

    def test_workshop_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop(
                start_date='2031-07-04T00:00:00',
                # Missing id, end_date and track
            )

        errors: list[dict[str, Any]] = exc_info.value.errors()
        missing_fields: set[str] = {str(error['loc'][0]) for error in errors}
        assert 'id' in missing_fields
        assert 'end_date' in missing_fields
        assert 'track' in missing_fields

    def test_workshop_retrofit_stations_validation(self) -> None:
        """Test that retrofit_stations must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop(
                id='WS_TEST_03',
                start_date='2031-07-04T00:00:00',
                end_date='2031-07-25T23:59:59',
                retrofit_stations=0,
                track='track_10',
            )

        error: dict[str, Any] = exc_info.value.errors()[0]
        assert error['type'] == 'greater_than_equal'
        assert 'retrofit_stations' in error['loc']

    def test_workshop_worker_validation(self) -> None:
        """Test that worker must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            Workshop(
                id='WS_TEST_04',
                start_date='2031-07-04T00:00:00',
                end_date='2031-07-25T23:59:59',
                track='track_10',
                worker=0,
            )

        error: dict[str, Any] = exc_info.value.errors()[0]
        assert error['type'] == 'greater_than_equal'
        assert 'worker' in error['loc']

    def test_workshop_negative_retrofit_stations(self) -> None:
        """Test that negative retrofit_stations are invalid."""
        with pytest.raises(ValidationError):
            Workshop(
                id='WS_TEST_05',
                start_date='2031-07-04T00:00:00',
                end_date='2031-07-25T23:59:59',
                retrofit_stations=-1,
                track='track_10',
            )

    def test_workshop_negative_worker(self) -> None:
        """Test that negative worker count is invalid."""
        with pytest.raises(ValidationError):
            Workshop(
                id='WS_TEST_06',
                start_date='2031-07-04T00:00:00',
                end_date='2031-07-25T23:59:59',
                worker=-2,
                track='track_10',
            )

    @pytest.mark.parametrize('stations', [1, 2, 5, 10, 100])
    def test_workshop_valid_retrofit_stations(self, stations: int) -> None:
        """Test various valid retrofit_stations values.

        Parameters
        ----------
        stations : int
            Number of retrofit stations to test.
        """
        workshop: Workshop = Workshop(
            id=f'WS_TEST_{stations}',
            start_date='2031-07-04T00:00:00',
            end_date='2031-07-25T23:59:59',
            retrofit_stations=stations,
            track='track_10',
        )

        assert workshop.retrofit_stations == stations

    @pytest.mark.parametrize('workers', [1, 2, 4, 8, 20])
    def test_workshop_valid_worker_counts(self, workers: int) -> None:
        """Test various valid worker counts.

        Parameters
        ----------
        workers : int
            Number of workers to test.
        """
        workshop: Workshop = Workshop(
            id=f'WS_TEST_W{workers}',
            start_date='2031-07-04T00:00:00',
            end_date='2031-07-25T23:59:59',
            worker=workers,
            track='track_10',
        )

        assert workshop.worker == workers

    def test_workshop_from_dict(self) -> None:
        """Test creating workshop from dictionary."""
        workshop_data: dict[str, Any] = {
            'id': 'WS_TEST_DICT',
            'start_date': '2031-07-04T00:00:00',
            'end_date': '2031-07-25T23:59:59',
            'retrofit_stations': 3,
            'track': 'track_7',
            'worker': 6,
        }

        workshop: Workshop = Workshop(**workshop_data)

        assert workshop.id == 'WS_TEST_DICT'
        assert workshop.start_date == '2031-07-04T00:00:00'
        assert workshop.end_date == '2031-07-25T23:59:59'
        assert workshop.retrofit_stations == 3
        assert workshop.track == 'track_7'
        assert workshop.worker == 6

    def test_workshop_model_dump(self) -> None:
        """Test converting workshop to dictionary."""
        workshop: Workshop = Workshop(
            id='WS_TEST_DUMP',
            start_date='2031-07-11T00:00:00',
            end_date='2031-07-25T23:59:59',
            retrofit_stations=2,
            track='track_Z1',
            worker=4,
        )

        workshop_dict: dict[str, Any] = workshop.model_dump()

        assert workshop_dict['id'] == 'WS_TEST_DUMP'
        assert workshop_dict['start_date'] == '2031-07-11T00:00:00'
        assert workshop_dict['end_date'] == '2031-07-25T23:59:59'
        assert workshop_dict['retrofit_stations'] == 2
        assert workshop_dict['track'] == 'track_Z1'
        assert workshop_dict['worker'] == 4

    def test_workshop_date_format(self) -> None:
        """Test that various ISO date formats are accepted."""
        workshop: Workshop = Workshop(
            id='WS_TEST_DATE',
            start_date='2031-07-04',
            end_date='2031-07-25T23:59:59.999Z',
            track='track_10',
        )

        assert workshop.start_date == '2031-07-04'
        assert workshop.end_date == '2031-07-25T23:59:59.999Z'

    def test_load_workshop_from_fixtures_file(self, fixtures_path: Path) -> None:
        """Test loading workshop from JSON fixture file.

        Parameters
        ----------
        fixtures_path : Path
            Path to fixtures directory.
        """
        fixtures_workshops_json_path: Path = fixtures_path / 'workshops.json'

        with fixtures_workshops_json_path.open(encoding='utf-8') as f:
            workshops_data: dict[str, str] = json.load(f)

        workshops_list: list[dict[str, str]] = workshops_data.get('workshops')
        workshops: list[Workshop] = [Workshop(**data) for data in workshops_list]

        assert len(workshops) == 2
        assert workshops[0].id == 'WS_01'
        assert workshops[0].track == 'track_Z1'
        assert workshops[1].id == 'WS_02'
        assert workshops[1].retrofit_stations == 3
        assert workshops[1].worker == 6
