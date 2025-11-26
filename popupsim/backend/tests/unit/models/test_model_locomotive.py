"""Unit tests for locomotive model."""

from datetime import UTC
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError
import pytest
from workshop_operations.domain.entities.locomotive import Locomotive


def test_locomotive_creation() -> None:
    """Test creating a locomotive with valid data."""
    loc = Locomotive(
        locomotive_id='WS_01',
        name='Secondary locomotive',
        start_date='2031-07-04 01:30:00',
        end_date='2031-07-05 02:00:00',
        track_id='track_19',
    )
    assert loc.locomotive_id == 'WS_01'
    assert loc.name == 'Secondary locomotive'
    assert loc.track_id == 'track_19'


def test_locomotive_with_datetime_objects() -> None:
    """Test creating a locomotive with datetime objects."""
    start = datetime(2031, 7, 4, 1, 30, 0, tzinfo=UTC)
    end = datetime(2031, 7, 5, 2, 0, 0, tzinfo=UTC)
    loc = Locomotive(
        locomotive_id='WS_02',
        name='Test',
        start_date=start,
        end_date=end,
        track_id='track_20',
    )
    assert loc.start_date == start
    assert loc.end_date == end


def test_locomotive_invalid_datetime_format() -> None:
    """Test locomotive with invalid datetime format."""
    with pytest.raises(ValidationError, match='start_date'):
        Locomotive(
            locomotive_id='WS_03',
            name='Test',
            start_date='invalid-date',
            end_date='2031-07-05 02:00:00',
            track_id='track_21',
        )


def test_locomotive_load_from_fixture(fixtures_path: Path) -> None:
    """Test loading locomotive data from a fixture file."""
    import json

    fixture_file = fixtures_path / 'locomotive.json'
    with fixture_file.open('r') as f:
        locomotive_data = json.load(f)

    locomotive_list: list[dict[str, str]] = locomotive_data.get('locomotives')
    loc_data = locomotive_list[0]

    loc = Locomotive(**loc_data)
    assert loc.locomotive_id == loc_data.get('locomotive_id')
    assert loc.name == loc_data.get('name')
    assert loc.track_id == loc_data.get('track_id')
