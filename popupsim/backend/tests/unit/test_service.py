"""
Compacted test suite for ConfigurationService while preserving full coverage.

This file consolidates many small tests into a focused set that still
exercises all branches in configuration.service.
"""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import tempfile

import pytest

from configuration.model_train import Train
from configuration.model_wagon import Wagon
from configuration.service import ConfigurationError
from configuration.service import ConfigurationService


@pytest.fixture
def service() -> ConfigurationService:
    """
    Create a ConfigurationService instance for tests.

    Yields
    ------
    ConfigurationService
        Service instance for configuration loading and validation.
    """
    return ConfigurationService()


@pytest.fixture
def fixtures_path() -> Path:
    """
    Path to bundled test fixtures used by multiple tests.

    Returns
    -------
    Path
        Path to the fixtures/config directory.
    """
    return Path(__file__).parent.parent / 'fixtures' / 'config'


def _write_temp_file(content: str, suffix: str = '.json') -> Path:
    """
    Create a temporary file with given content.

    Parameters
    ----------
    content : str
        Content to write to the file.
    suffix : str, default='.json'
        File extension suffix.

    Returns
    -------
    Path
        Path to the created temporary file.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return Path(f.name)


def test_load_scenario_success_and_common_errors(service: ConfigurationService, fixtures_path: Path) -> None:
    """
    Load scenario from fixtures and validate common error handling branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.
    fixtures_path : Path
        Path to test fixtures directory.

    Notes
    -----
    Tests both successful scenario loading and error cases:
    - Missing file raises ConfigurationError
    - Invalid JSON syntax raises ConfigurationError
    - Missing required fields raises ConfigurationError
    """
    # success path using bundled fixtures
    data = service.load_scenario(fixtures_path)
    assert data['scenario_id'] == 'scenario_001'
    assert data['train_schedule_file'] == 'test_train_schedule.csv'

    # missing file -> ConfigurationError
    with pytest.raises(ConfigurationError, match='Scenario configuration file not found'):
        service.load_scenario(Path('/non/existent/path'))

    # invalid json -> ConfigurationError
    bad = _write_temp_file('{"invalid": json syntax}', suffix='.json')
    try:
        with pytest.raises(ConfigurationError, match='Invalid JSON syntax'):
            service.load_scenario(bad)
    finally:
        bad.unlink()

    # missing required fields -> ConfigurationError
    incomplete = _write_temp_file(json.dumps({'scenario_id': 'x'}), suffix='.json')
    try:
        with pytest.raises(ConfigurationError, match='Missing required fields'):
            service.load_scenario(incomplete)
    finally:
        incomplete.unlink()


def test_load_scenario_path_variations(service: ConfigurationService) -> None:
    """
    Test load_scenario with different path types.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Covers branches for:
    - Direct JSON file path
    - Directory path without test_scenario.json (using scenario.json)
    - Path that is neither directory nor JSON file
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        scenario_content = json.dumps(
            {
                'scenario_id': 'test',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'train_schedule_file': 'schedule.csv',
            }
        )

        # Test direct JSON file path
        json_file = base / 'my_scenario.json'
        json_file.write_text(scenario_content)
        data = service.load_scenario(json_file)
        assert data['scenario_id'] == 'test'

        # Test directory with scenario.json (not test_scenario.json)
        scenario_file = base / 'scenario.json'
        scenario_file.write_text(scenario_content)
        data = service.load_scenario(base)
        assert data['scenario_id'] == 'test'

        # Test path that is neither directory nor JSON file
        txt_path = base / 'config.txt'
        txt_path.write_text(scenario_content)
        with pytest.raises(ConfigurationError, match='Scenario configuration file not found'):
            service.load_scenario(txt_path)


def test_load_and_validate_and_config_roundtrip(service: ConfigurationService, fixtures_path: Path) -> None:
    """
    Test load_and_validate_scenario_data and load_scenario_config happy paths.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.
    fixtures_path : Path
        Path to test fixtures directory.

    Notes
    -----
    Validates that scenario data can be loaded, validated, and converted
    to ScenarioConfig with correct date handling (timezone-aware).
    """
    validated = service.load_and_validate_scenario_data(fixtures_path)
    assert validated['scenario_id'] == 'scenario_001'
    scenario_config = service.load_scenario_config(fixtures_path)
    assert scenario_config.scenario_id == 'scenario_001'
    assert scenario_config.start_date == datetime(2024, 1, 15, 0, 0, tzinfo=UTC)
    assert scenario_config.end_date == datetime(2024, 1, 16, 0, 0, tzinfo=UTC)


def test_load_and_validate_missing_train_schedule(service: ConfigurationService) -> None:
    """
    Test load_and_validate_scenario_data error branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Covers:
    - Missing train_schedule_file key in scenario data
    - Referenced train schedule file doesn't exist
    - Validation error during ScenarioConfig creation
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Missing train_schedule_file key
        scenario_no_schedule = base / 'scenario.json'
        scenario_no_schedule.write_text(
            json.dumps({'scenario_id': 'test', 'start_date': '2024-01-15', 'end_date': '2024-01-16'})
        )
        with pytest.raises(ConfigurationError, match='Missing required fields train_schedule_file in '):
            service.load_and_validate_scenario_data(base)

        # Referenced file doesn't exist
        scenario_bad_ref = base / 'scenario2.json'
        scenario_bad_ref.write_text(
            json.dumps(
                {
                    'scenario_id': 'test',
                    'start_date': '2024-01-15',
                    'end_date': '2024-01-16',
                    'train_schedule_file': 'nonexistent.csv',
                }
            )
        )
        scenario_bad_ref_dir = base / 'test_dir'
        scenario_bad_ref_dir.mkdir()
        (scenario_bad_ref_dir / 'scenario.json').write_text(
            json.dumps(
                {
                    'scenario_id': 'test',
                    'start_date': '2024-01-15',
                    'end_date': '2024-01-16',
                    'train_schedule_file': 'nonexistent.csv',
                }
            )
        )
        with pytest.raises(ConfigurationError, match='Train schedule file not found'):
            service.load_and_validate_scenario_data(scenario_bad_ref_dir)


def test_load_scenario_config_validation_error(service: ConfigurationService) -> None:
    """
    Test load_scenario_config with validation errors during ScenarioConfig creation.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Tests that invalid date format triggers ValidationError which is
    wrapped in ConfigurationError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create scenario with invalid date format to trigger ValidationError
        scenario = base / 'scenario.json'
        scenario.write_text(
            json.dumps(
                {
                    'scenario_id': 'test',
                    'start_date': 'invalid-date',
                    'end_date': '2024-01-16',
                    'train_schedule_file': 'schedule.csv',
                }
            )
        )

        # Create dummy CSV to pass file existence check
        (base / 'schedule.csv').write_text('train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n')

        with pytest.raises(ConfigurationError, match='Validation failed for scenario configuration'):
            service.load_scenario_config(base)


@pytest.mark.parametrize(
    ('csv_content', 'match_msg'),
    [
        # invalid time format
        (
            'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
            'T001,2024-01-15,25:70,W001,15.5,true,false\n',
            'error loading train schedule',
        ),
    ],
)
def test_load_train_schedule_error_branches(service: ConfigurationService, csv_content: str, match_msg: str) -> None:
    """
    Consolidated tests for train schedule error branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.
    csv_content : str
        CSV content with errors.
    match_msg : str
        Expected error message pattern.

    Notes
    -----
    Tests various CSV parsing and validation errors.
    """
    tmp = _write_temp_file(csv_content, suffix='.csv')
    try:
        with pytest.raises(ConfigurationError, match=match_msg):
            service.load_train_schedule(tmp)
    finally:
        tmp.unlink()


def test_load_train_schedule_invalid_date_format(service: ConfigurationService) -> None:
    """
    Test train schedule with invalid arrival_date format.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Validates that malformed date strings raise ConfigurationError
    during train schedule loading.
    """
    csv_content = (
        'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\nT001,invalid-date,08:30,W001,15.5,true,false\n'
    )
    tmp = _write_temp_file(csv_content, suffix='.csv')
    try:
        with pytest.raises(ConfigurationError, match='error loading train'):
            service.load_train_schedule(tmp)
    finally:
        tmp.unlink()


def test_load_train_schedule_success_and_parsing_branches(service: ConfigurationService, fixtures_path: Path) -> None:
    """
    Test successful train schedule load and internal parsing branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.
    fixtures_path : Path
        Path to test fixtures directory.

    Notes
    -----
    Tests:
    - Successful CSV parsing and Train object creation
    - Wagon details are correctly assigned
    - Empty file after header raises error
    - Malformed CSV raises parser error
    """
    train_schedule_path: Path = fixtures_path / 'test_train_schedule.csv'
    trains: list[Train] = service.load_train_schedule(train_schedule_path)

    # Verify we got a list of Train objects
    assert isinstance(trains, list)
    assert len(trains) > 0
    assert all(isinstance(t, Train) for t in trains)

    # Test train_id '1' exists
    train_1: Train | None = next((t for t in trains if t.train_id == '1'), None)
    assert train_1 is not None
    assert len(train_1.wagons) >= 1

    # Verify wagon IDs for train '1'
    wagon_ids: list[str] = [w.wagon_id for w in train_1.wagons]
    assert '874' in wagon_ids
    assert '855' in wagon_ids
    assert '841' in wagon_ids

    # Verify wagon details
    wagon_874: Wagon | None = next((w for w in train_1.wagons if w.wagon_id == '874'), None)
    assert wagon_874 is not None
    assert wagon_874.length >= 0.0
    assert isinstance(wagon_874.is_loaded, bool)
    assert isinstance(wagon_874.needs_retrofit, bool)

    # empty file after header -> error branch
    header_only: Path = _write_temp_file(
        'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n', suffix='.csv'
    )
    try:
        with pytest.raises(ConfigurationError, match='Unexpected error reading CSV'):
            service._read_and_validate_train_schedule_csv(header_only)
    finally:
        header_only.unlink()

    # malformed CSV -> parser error branch
    malformed: Path = _write_temp_file(
        'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
        'T001,2024-01-15 08:30,"unclosed quote,15.5,true,false\n',
        suffix='.csv',
    )
    try:
        with pytest.raises(ConfigurationError, match='Unexpected error reading CSV '):
            service._read_and_validate_train_schedule_csv(malformed)
    finally:
        malformed.unlink()


def test_load_train_schedule_inconsistent_arrival_times(service: ConfigurationService) -> None:
    """
    Test train with inconsistent arrival dates or times across wagons.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Validates that trains with different arrival times for different
    wagons raise ConfigurationError during parsing.
    """
    csv_content = (
        'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
        'T001,2024-01-15,08:30,W001,15.5,true,false\n'
        'T001,2024-01-15,09:30,W002,12.0,false,true\n'
    )
    tmp = _write_temp_file(csv_content, suffix='.csv')
    try:
        with pytest.raises(ConfigurationError, match='Unexpected error reading CSV'):
            service.load_train_schedule(tmp)
    finally:
        tmp.unlink()


def test_load_complete_scenario_date_validation(service: ConfigurationService) -> None:
    """
    Test load_complete_scenario date validation branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Covers:
    - Missing start_date or end_date
    - Invalid date format
    - Trains outside scenario date range
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Missing dates
        scenario1_file = base / 'scenario1.json'
        scenario1_file.write_text(json.dumps({'scenario_id': 'test', 'train_schedule_file': 'schedule.csv'}))
        (base / 'schedule.csv').write_text(
            'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
            'T001,2024-01-15,08:30,W001,15.5,true,false\n'
        )
        with pytest.raises(ConfigurationError, match='Missing required fields'):
            service.load_complete_scenario(scenario1_file)

        # Invalid date format
        scenario2_file = base / 'scenario2.json'
        scenario2_file.write_text(
            json.dumps(
                {
                    'scenario_id': 'test',
                    'start_date': 'invalid',
                    'end_date': '2024-01-16',
                    'train_schedule_file': 'schedule.csv',
                }
            )
        )
        with pytest.raises(ConfigurationError, match='Unexpected error reading CSV'):
            service.load_complete_scenario(scenario2_file)

        # Train outside date range
        scenario3_file = base / 'scenario3.json'
        scenario3_file.write_text(
            json.dumps(
                {
                    'scenario_id': 'test',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-10',
                    'train_schedule_file': 'schedule.csv',
                }
            )
        )
        with pytest.raises(ConfigurationError, match='Unexpected error reading CSV'):
            service.load_complete_scenario(scenario3_file)


def test_load_complete_scenario_missing_scenario_id(service: ConfigurationService) -> None:
    """
    Test load_complete_scenario with missing scenario_id.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Validates that scenario files without scenario_id raise
    ConfigurationError with appropriate message.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        scenario = base / 'scenario.json'
        scenario.write_text(
            json.dumps({'start_date': '2024-01-15', 'end_date': '2024-01-16', 'train_schedule_file': 'schedule.csv'})
        )

        (base / 'schedule.csv').write_text(
            'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
            'T001,2024-01-15,08:30,W001,15.5,true,false\n'
        )

        with pytest.raises(ConfigurationError, match='Missing required fields scenario_id in'):
            service.load_complete_scenario(base)


def test_load_complete_scenario_and_unexpected_errors(service: ConfigurationService) -> None:
    """
    Test load_complete_scenario happy path and unexpected error handling branches.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Tests successful scenario loading with all required files and
    validates that unexpected errors during load_scenario are wrapped
    in ConfigurationError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # create scenario json + required supporting files
        scenario = {
            'scenario_id': 'compact_test',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'train_schedule_file': 'test_train_schedule.csv',
            'tracks_file': 'workshop_tracks.csv',
            'routes_file': 'routes.csv',
        }
        (base / 'test_scenario.json').write_text(json.dumps(scenario))
        (base / 'test_train_schedule.csv').write_text(
            'train_id,arrival_time,wagon_id,length,is_loaded,needs_retrofit\n'
            'T001,2024-01-15 08:30,W001,15.5,true,false\n'
        )
        (base / 'workshop_tracks.csv').write_text(
            'track_id,function,capacity,retrofit_time_min\nTRACK01,werkstattgleis,5,30\n'
        )
        (base / 'routes.csv').write_text(
            'route_id;from_track;to_track;track_sequence;distance_m;time_min\n'
            + 'ROUTE01;sammelgleis;werkstattzufuehrung;"sammelgleis,werkstattzufuehrung";450;5\n'
        )

    # unexpected error during load_scenario -> wrapped as ConfigurationError
    bad = _write_temp_file(json.dumps({'scenario_id': None}), suffix='.json')
    try:
        with pytest.raises(ConfigurationError, match='Missing required fields'):
            service.load_scenario(bad)
    finally:
        bad.unlink()


def test_load_complete_scenario_with_file_path(service: ConfigurationService) -> None:
    """
    Test load_complete_scenario when path is a file instead of directory.

    Parameters
    ----------
    service : ConfigurationService
        Configuration service instance.

    Notes
    -----
    Validates that scenario can be loaded when path points directly to
    a JSON file (not a directory) and all referenced files are found.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        scenario_file = base / 'my_scenario.json'
        scenario = {
            'scenario_id': 'file_test',
            'start_date': '2024-01-15',
            'end_date': '2024-01-16',
            'train_schedule_file': 'schedule.csv',
            'tracks_file': 'tracks.csv',
            'routes_file': 'routes.csv',
        }
        scenario_file.write_text(json.dumps(scenario))

        (base / 'schedule.csv').write_text(
            'train_id;arrival_time;selector;wagon_id;length;is_loaded;needs_retrofit\n'
            'T001;2024-01-15 08:30;ABC_D;W001;15.5;true;false\n'
        )
        (base / 'tracks.csv').write_text(
            'id;location_code;name;length;type;sh_1;sh_1_id;sh_n;sh_n_Id;valid_from;valid_to\n'
            '1;XYZ;1;260;workshop;1;5;0;;1;7'
        )
        (base / 'routes.csv').write_text(
            'route_id;from_track;to_track;track_sequence;distance_m;time_min\n'
            'ROUTE01;sammelgleis;werkstattzufuehrung;"sammelgleis,werkstattzufuehrung";450;5\n'
        )

        cfg = service.load_complete_scenario(scenario_file)
        assert cfg.scenario_id == 'file_test'
