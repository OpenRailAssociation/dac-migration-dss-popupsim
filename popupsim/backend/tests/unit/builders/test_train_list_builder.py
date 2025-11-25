"""Unit tests for TrainListParser class.

Tests for loading train schedules from CSV files and building train lists.
"""

from collections.abc import Generator
from datetime import UTC
from datetime import datetime
from pathlib import Path
import tempfile

from configuration.infrastructure.parsers.train_list_parser import TrainListParser
from configuration.domain.models.train import TRAIN_DEFAULT_ID
from configuration.domain.models.train import Train
from configuration.domain.models.wagon import Wagon
import pandas as pd
import pytest


@pytest.fixture
def temp_csv_file() -> Generator[Path]:
    """Create a temporary CSV file.

    Yields
    ------
    Path
        Path to temporary CSV file.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def valid_train_schedule(temp_csv_file: Path) -> Path:
    """Create a valid train schedule CSV file.

    Parameters
    ----------
    temp_csv_file : Path
        Temporary file path.

    Returns
    -------
    Path
        Path to CSV file with valid train schedule data.
    """
    content = (
        'train_id;wagon_id;length;Track;arrival_time;is_loaded;needs_retrofit\n'
        '1;W001;15.5;ABC_D;2024-01-15 10:30:00;true;false\n'
        '1;W002;12.3;ABC_D;2024-01-15 10:35:00;false;true\n'
        '2;W003;18.2;ABC_D;2024-01-15 14:20:00;true;true\n'
    )
    temp_csv_file.write_text(content)
    return temp_csv_file


@pytest.fixture
def schedule_with_empty_train_ids(temp_csv_file: Path) -> Path:
    """Create a schedule CSV with empty train IDs.

    Parameters
    ----------
    temp_csv_file : Path
        Temporary file path.

    Returns
    -------
    Path
        Path to CSV file with empty train_id fields.
    """
    content = (
        'train_id;wagon_id;length;Track;arrival_time;is_loaded;needs_retrofit\n'
        ';W001;15.5;ABC_D;2024-01-15 10:30:00;true;false\n'
        ';W002;12.3;ABC_D;2024-01-15 10:35:00;false;true\n'
    )
    temp_csv_file.write_text(content)
    return temp_csv_file


@pytest.mark.unit
class TestTrainListBuilder:
    """Test suite for TrainListParser class."""

    def test_init_creates_empty_list(self, temp_csv_file: Path) -> None:
        """Test that initialization creates empty train list.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        builder: TrainListParser = TrainListParser(temp_csv_file)

        assert builder.trains == []
        assert builder.schedule_path == temp_csv_file

    def test_load_csv_success(self, valid_train_schedule: Path) -> None:
        """Test successful CSV loading.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)

        df: pd.DataFrame = builder._load_csv()

        assert len(df) == 3
        assert 'train_id' in df.columns
        assert 'arrival_time' in df.columns
        assert df['train_id'].dtype == object

    def test_load_csv_nonexistent_file(self, temp_csv_file: Path) -> None:
        """Test loading from nonexistent file raises error.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        nonexistent: Path = temp_csv_file.parent / 'nonexistent.csv'
        builder: TrainListParser = TrainListParser(nonexistent)

        with pytest.raises(FileNotFoundError, match='Schedule file not found'):
            builder._load_csv()

    def test_load_csv_invalid_format(self, temp_csv_file: Path) -> None:
        """Test loading CSV with invalid format.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        temp_csv_file.write_text('invalid;csv;format\nwith;wrong;structure')
        builder: TrainListParser = TrainListParser(temp_csv_file)

        with pytest.raises(ValueError, match='Failed to parse CSV file'):
            builder._load_csv()

    def test_load_csv_fills_empty_train_ids(self, schedule_with_empty_train_ids: Path) -> None:
        """Test that empty train_id fields are filled with default value.

        Parameters
        ----------
        schedule_with_empty_train_ids : Path
            Path to CSV with empty train_id fields.
        """
        builder: TrainListParser = TrainListParser(schedule_with_empty_train_ids)

        df: pd.DataFrame = builder._load_csv()

        assert all(df['train_id'] == TRAIN_DEFAULT_ID)
        assert df['train_id'].dtype == object

    def test_create_trains_from_dataframe_single_train(self, valid_train_schedule: Path) -> None:
        """Test creating trains from DataFrame with single train.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)
        df: pd.DataFrame = builder._load_csv()
        df_single_train: pd.DataFrame = df[df['train_id'] == '1']

        trains: list[Train] = builder._create_trains_from_dataframe(df_single_train)

        assert len(trains) == 1
        assert trains[0].train_id == '1'
        assert len(trains[0].wagons) == 2
        assert trains[0].arrival_time.date() == datetime(2024, 1, 15, 10, 35, 0, tzinfo=UTC).date()

    def test_create_trains_from_dataframe_multiple_trains(self, valid_train_schedule: Path) -> None:
        """Test creating trains from DataFrame with multiple trains.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)
        df: pd.DataFrame = builder._load_csv()

        trains: list[Train] = builder._create_trains_from_dataframe(df)

        assert len(trains) == 2
        assert trains[0].train_id == '1'
        assert trains[1].train_id == '2'
        assert len(trains[0].wagons) == 2
        assert len(trains[1].wagons) == 1

    def test_create_trains_uses_latest_arrival_time(self, valid_train_schedule: Path) -> None:
        """Test that train uses latest arrival time from its wagons.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)
        df: pd.DataFrame = builder._load_csv()

        trains: list[Train] = builder._create_trains_from_dataframe(df)

        train_1: Train = next(t for t in trains if t.train_id == '1')
        # Latest arrival is 10:35:00, not 10:30:00
        assert train_1.arrival_time.date() == datetime(2024, 1, 15, 10, 35, 0, tzinfo=UTC).date()

    def test_create_trains_wagon_properties(self, valid_train_schedule: Path) -> None:
        """Test that wagon properties are correctly assigned.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)
        df: pd.DataFrame = builder._load_csv()

        trains: list[Train] = builder._create_trains_from_dataframe(df)

        train_1: Train = next(t for t in trains if t.train_id == '1')
        wagon_1: Wagon = next(w for w in train_1.wagons if w.wagon_id == 'W001')

        assert wagon_1.length == 15.5
        assert wagon_1.is_loaded is True
        assert wagon_1.needs_retrofit is False

    def test_create_trains_invalid_data(self, temp_csv_file: Path) -> None:
        """Test creating trains with invalid wagon data.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        content = (
            'train_id;wagon_id;length;Track;arrival_time;is_loaded;needs_retrofit\n'
            '1;W001;invalid;ABC_D;2024-01-15 10:30:00;true;false\n'
        )
        temp_csv_file.write_text(content)
        builder: TrainListParser = TrainListParser(temp_csv_file)
        df: pd.DataFrame = builder._load_csv()

        with pytest.raises(ValueError, match='Failed to create train'):
            builder._create_trains_from_dataframe(df)

    def test_build_success(self, valid_train_schedule: Path) -> None:
        """Test successful build of train list.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)

        trains: list[Train] = builder.build()

        assert len(trains) == 2
        assert all(isinstance(train, Train) for train in trains)
        assert builder.trains == trains

    def test_build_stores_trains_in_instance(self, valid_train_schedule: Path) -> None:
        """Test that build stores trains in instance variable.

        Parameters
        ----------
        valid_train_schedule : Path
            Path to valid train schedule CSV.
        """
        builder: TrainListParser = TrainListParser(valid_train_schedule)

        assert builder.trains == []

        trains: list[Train] = builder.build()

        assert builder.trains == trains
        assert len(builder.trains) == 2

    def test_build_with_nonexistent_file(self, temp_csv_file: Path) -> None:
        """Test build with nonexistent file raises error.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        nonexistent: Path = temp_csv_file.parent / 'nonexistent.csv'
        builder: TrainListParser = TrainListParser(nonexistent)

        with pytest.raises(FileNotFoundError):
            builder.build()

    def test_build_with_complex_schedule(self, temp_csv_file: Path) -> None:
        """Test build with complex schedule containing multiple trains.

        Parameters
        ----------
        temp_csv_file : Path
            Temporary file path.
        """
        content = (
            'train_id;wagon_id;length;Track;arrival_time;is_loaded;needs_retrofit\n'
            'T001;W001;15.5;ABC_D;2024-01-15 10:30:00;true;false\n'
            'T001;W002;12.3;ABC_D;2024-01-15 10:35:00;false;true\n'
            'T001;W003;18.2;ABC_D;2024-01-15 10:40:00;true;true\n'
            'T002;W004;20.0;ABC_D;2024-01-15 14:20:00;false;false\n'
            'T002;W005;11.5;ABC_D;2024-01-15 14:25:00;true;false\n'
            'T003;W006;16.8;ABC_D;2024-01-15 18:00:00;true;true\n'
        )
        temp_csv_file.write_text(content)
        builder: TrainListParser = TrainListParser(temp_csv_file)

        trains: list[Train] = builder.build()

        assert len(trains) == 3
        assert sum(len(t.wagons) for t in trains) == 6

        train_t001: Train = next(t for t in trains if t.train_id == 'T001')
        assert len(train_t001.wagons) == 3
        assert train_t001.arrival_time.date() == datetime(2024, 1, 15, 10, 40, 0, tzinfo=UTC).date()

    def test_load_trains_list_from_fixtures_file(self, fixtures_path: Path) -> None:
        """Test loading trains list from fixtures file.

        Parameters
        ----------
        fixtures_path : Path
            Path to fixtures directory.

        Generic test loading the test_train_schedule file from the fixtures directory.
        """
        schedule_file: Path = fixtures_path / 'test_train_schedule.csv'
        trains: list[Train] = TrainListParser(schedule_file).build()

        assert len(trains) == 2
        assert all(isinstance(train, Train) for train in trains)
