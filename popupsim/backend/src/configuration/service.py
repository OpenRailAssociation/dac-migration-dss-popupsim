"""
Configuration service for loading, validating, and managing train simulation data.

This module provides the ConfigurationService class that handles:
- Loading and validating scenario configurations from JSON files
- Loading and parsing train schedule data from CSV files
- Creating validated domain models (ScenarioConfig, Train, Wagon)
- Cross-validation between scenario dates and train arrival dates
- Comprehensive error handling and logging for configuration issues
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, List, Optional, Union

import pandas as pd
from pydantic import ValidationError

from .model_routes import RoutesConfig
from .model_scenario import ScenarioConfig
from .model_track import TrackFunction, WorkshopTrack
from .model_train import Train
from .model_wagon import Wagon
from .model_workshop import Workshop

# Configure logging
logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


class ConfigurationService:
    """Service for loading and validating configuration files."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the configuration service.
        Args:
            base_path: Base directory for configuration files. Defaults to current directory.
        """
        self.base_path = base_path or Path.cwd()

    def load_scenario(self, path: Union[str, Path]) -> dict[str, Any]:
        """
        Load scenario configuration from a JSON file.
        Args:
            path: Directory path containing scenario.json or direct path to JSON file
        Returns:
            dict[str, Any]: Scenario configuration data
        """
        path = Path(path)

        # Handle both directory and file paths
        if path.is_dir():
            # First try test_scenario.json for test fixtures, then fallback to scenario.json
            test_file_path = path / 'test_scenario.json'
            file_path = test_file_path if test_file_path.exists() else path / 'scenario.json'
        elif path.suffix == '.json':
            file_path = path
        else:
            # First try test_scenario.json for test fixtures, then fallback to scenario.json
            test_file_path = path / 'test_scenario.json'
            file_path = test_file_path if test_file_path.exists() else path / 'scenario.json'

        if not file_path.exists():
            raise ConfigurationError(f'Scenario configuration file not found: {file_path}')

        logger.info('Loading scenario configuration from %s', file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields exist before creating model
            required_fields = ['scenario_id', 'start_date', 'end_date', 'train_schedule_file']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ConfigurationError(
                    f'Missing required fields in {file_path}: '
                    f'{", ".join(missing_fields)}. Found fields: {", ".join(data.keys())}'
                )

            logger.info('Successfully loaded scenario: %s', data.get('scenario_id'))
            return data

        except json.JSONDecodeError as e:
            error_msg = (
                f'Invalid JSON syntax in {file_path} at line {e.lineno}, column {e.colno}: {e.msg}. '
                'Please check the JSON structure and ensure all brackets and quotes are properly closed.'
            )
            logger.error('%s', error_msg)
            raise ConfigurationError(error_msg) from e
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field_path = ' -> '.join(str(loc) for loc in error['loc'])
                error_details.append(f"Field '{field_path}': {error['msg']} (input: {error.get('input', 'N/A')})")
            error_msg = (
                f'Validation failed for scenario configuration in {file_path}:\n'
                f'  • {chr(10).join("  • " + detail for detail in error_details)}'
            )
            logger.error('%s', error_msg)
            raise ConfigurationError(error_msg) from e
        except Exception as e:
            error_msg = f'Unexpected error loading {file_path}: {e}'
            logger.error('%s', error_msg)
            raise ConfigurationError(error_msg) from e

    def load_and_validate_scenario(self, path: Union[str, Path]) -> dict[str, Any]:
        """
        Load scenario configuration and validate all referenced files exist.
        Args:
            path: Directory path containing scenario.json
        Returns:
            dict[str, Any]: Validated scenario configuration data
        """
        scenario_data = self.load_scenario(path)
        config_dir = Path(path) if isinstance(path, str) else path

        if config_dir.is_file():
            config_dir = config_dir.parent

        # Validate referenced files exist
        train_schedule_file = scenario_data.get('train_schedule_file')
        if not train_schedule_file:
            raise ConfigurationError('Missing train_schedule_file in scenario configuration')

        train_schedule_path = config_dir / train_schedule_file
        if not train_schedule_path.exists():
            raise ConfigurationError(f'Train schedule file not found: {train_schedule_path}')

        logger.info('All referenced files validated for json scenario data: %s', scenario_data.get('scenario_id'))
        return scenario_data

    def _read_and_validate_train_schedule_csv(self, file_path: Path) -> pd.DataFrame:
        """Read CSV and validate required columns and emptiness."""
        try:
            df = pd.read_csv(
                file_path,
                dtype={'train_id': str, 'wagon_id': str, 'length': float, 'arrival_time': str},
                converters={
                    'is_loaded': self.to_bool,
                    'needs_retrofit': self.to_bool,
                },
                parse_dates=['arrival_date'],
                date_format='%Y-%m-%d',
            )
            # Check that the loaded object is a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                raise ConfigurationError(f'Loaded object is not a pandas DataFrame: got {type(df)}')
        except pd.errors.EmptyDataError as err:
            raise ConfigurationError('Train schedule file is empty') from err
        except (pd.errors.ParserError, TypeError) as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err
        if df.empty:
            raise ConfigurationError('Train schedule file is empty')
        required_columns = [
            'train_id',
            'arrival_date',
            'arrival_time',
            'wagon_id',
            'length',
            'is_loaded',
            'needs_retrofit',
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ConfigurationError(
                f'Missing required columns in {file_path}: '
                f'{", ".join(missing_columns)}. Found columns: {", ".join(df.columns)}'
            )
        # Validate arrival_date format
        if not pd.api.types.is_datetime64_any_dtype(df['arrival_date']):
            raise ConfigurationError("Column 'arrival_date' must be in YYYY-MM-DD format.")

        # Validate arrival_time format
        invalid_times = df[~df['arrival_time'].astype(str).str.match(r'^[0-2][0-9]:[0-5][0-9]$')]
        if not invalid_times.empty:
            raise ConfigurationError(
                f"Column 'arrival_time' must be in HH:MM format. Invalid values:"
                f' {", ".join(map(str, invalid_times["arrival_time"].unique()))}'
            )
        return df

    @staticmethod
    def to_bool(value: Any) -> bool:
        """Robustly convert a value to boolean for CSV converters."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() == 'true'
        return False

    def _create_wagons_from_group(self, group: pd.DataFrame) -> List[Wagon]:
        """Create Wagon objects from a train group."""
        wagons = []
        for _, row in group.iterrows():
            try:
                wagon = Wagon(
                    wagon_id=str(row['wagon_id']),  # Use wagon_id directly
                    train_id=str(row['train_id']),
                    length=float(row['length']),
                    is_loaded=bool(row['is_loaded']),
                    needs_retrofit=bool(row['needs_retrofit']),
                )
                wagons.append(wagon)
            except ValidationError as err:
                error_details = []
                for error in err.errors():
                    field_path = ' -> '.join(str(loc) for loc in error['loc'])
                    error_details.append(f"Field '{field_path}': {error['msg']}")
                raise ConfigurationError(
                    f'Validation failed for wagon in train {row["train_id"]} in {row["wagon_id"]}:\n'
                    f'  • {chr(10).join("  • " + detail for detail in error_details)}'
                ) from err
        return wagons

    def _parse_arrival_time(self, df: pd.DataFrame) -> None:
        """Parse arrival time column in DataFrame."""
        try:
            df['arrival_time'] = pd.to_datetime(df['arrival_time'], format='%H:%M').dt.time
        except ValueError as err:
            raise ConfigurationError(f'Invalid time format in arrival_time. Expected HH:MM format: {err}') from err

    def _check_duplicate_wagons(self, df: pd.DataFrame) -> None:
        """Check for duplicate wagon IDs in DataFrame."""
        duplicate_wagons = df[df.duplicated(subset=['wagon_id'], keep=False)]['wagon_id'].unique()
        if len(duplicate_wagons) > 0:
            raise ConfigurationError(f'Duplicate wagon IDs found: {", ".join(duplicate_wagons)}')

    def _validate_train_consistency(self, train_id: str, group: pd.DataFrame) -> None:
        """Validate that train has consistent arrival date/time across wagons."""
        unique_dates = group['arrival_date'].nunique()
        unique_times = group['arrival_time'].nunique()
        if unique_dates > 1 or unique_times > 1:
            raise ConfigurationError(f'Train {train_id} has inconsistent arrival date/time across wagons')

    def _convert_arrival_date(self, arrival_date_value: Any) -> date:
        """Convert pandas Timestamp or string to Python date object."""
        if hasattr(arrival_date_value, 'date'):
            return arrival_date_value.date()
        if isinstance(arrival_date_value, str):
            return date.fromisoformat(arrival_date_value)
        return arrival_date_value

    def _handle_train_validation_error(self, train_id: str, err: ValidationError) -> None:
        """Handle validation errors when creating Train objects."""
        error_details = []
        for error in err.errors():
            field_path = ' -> '.join(str(loc) for loc in error['loc'])
            error_details.append(f"Field '{field_path}': {error['msg']}")
        raise ConfigurationError(
            f'Validation failed for train arrival {train_id}:\n'
            f'  • {chr(10).join("  • " + detail for detail in error_details)}'
        ) from err

    def _create_train_arrivals(self, df: pd.DataFrame) -> List[Train]:
        """Group by train and create Train objects."""
        self._parse_arrival_time(df)
        self._check_duplicate_wagons(df)

        trains = []
        for train_id, group in df.groupby('train_id'):
            self._validate_train_consistency(str(train_id), group)
            wagons = self._create_wagons_from_group(group)

            try:
                arrival_date = self._convert_arrival_date(group.iloc[0]['arrival_date'])
                train = Train(
                    train_id=str(train_id),
                    arrival_date=arrival_date,
                    arrival_time=group.iloc[0]['arrival_time'],
                    wagons=wagons,
                )
                trains.append(train)
            except ValidationError as err:
                self._handle_train_validation_error(str(train_id), err)
        return trains

    def load_train_schedule(self, file_path: Union[str, Path]) -> List[Train]:
        """
        Load train schedule from CSV file and validate data.
        Args:
            file_path: Path to the train schedule CSV file
        Returns:
            List[Train]: Validated train arrivals with wagon information
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ConfigurationError(f'Train schedule file not found: {file_path}')
        logger.info('Loading train schedule from %s', file_path)
        try:
            df = self._read_and_validate_train_schedule_csv(file_path)
            train_arrivals = self._create_train_arrivals(df)
            logger.info('Successfully loaded %d trains with %d wagons from %s', len(train_arrivals), len(df), file_path)
            return train_arrivals
        except ConfigurationError as err:
            raise err
        except Exception as err:
            raise ConfigurationError(f'Unexpected error loading train schedule from {file_path}: {err}') from err

    def _create_workshop_tracks_from_dataframe(self, df: pd.DataFrame) -> List[WorkshopTrack]:
        """Create WorkshopTrack objects from DataFrame rows."""
        tracks = []
        for _, row in df.iterrows():
            try:
                track = WorkshopTrack(
                    id=str(row['track_id']).strip(),
                    function=TrackFunction(str(row['function']).strip()),
                    capacity=int(row['capacity']),
                    retrofit_time_min=int(row['retrofit_time_min']),
                )
                tracks.append(track)
            except ValidationError as err:
                error_details = []
                for error in err.errors():
                    field_path = ' -> '.join(str(loc) for loc in error['loc'])
                    error_details.append(f"Field '{field_path}': {error['msg']}")
                raise ConfigurationError(
                    f'Validation failed for track {row["track_id"]}:\n'
                    f'  • {chr(10).join("  • " + detail for detail in error_details)}'
                ) from err
            except (ValueError, TypeError) as err:
                raise ConfigurationError(f'Invalid data type for track {row["track_id"]}: {err}') from err
        return tracks

    def _read_and_validate_workshop_tracks_csv(self, file_path: Path) -> pd.DataFrame:
        """Read and validate workshop tracks CSV file."""
        try:
            # Read CSV with appropriate data types - expect track_id column
            df = pd.read_csv(
                file_path, dtype={'track_id': str, 'function': str, 'capacity': int, 'retrofit_time_min': int}
            )

            # Check that the loaded object is a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                raise ConfigurationError(f'Loaded object is not a pandas DataFrame: got {type(df)}')

            if df.empty:
                raise ConfigurationError('Workshop tracks file is empty')

            # Validate required columns - expect track_id instead of id
            required_columns = ['track_id', 'function', 'capacity', 'retrofit_time_min']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ConfigurationError(
                    f'Missing required columns in {file_path}: '
                    f'{", ".join(missing_columns)}. Found columns: {", ".join(df.columns)}'
                )

            # Check for duplicate track IDs - use track_id column
            duplicate_ids = df[df.duplicated(subset=['track_id'], keep=False)]['track_id'].unique()
            if len(duplicate_ids) > 0:
                raise ConfigurationError(f'Duplicate track IDs found: {", ".join(duplicate_ids)}')

            return df

        except pd.errors.EmptyDataError as err:
            raise ConfigurationError('Workshop tracks file is empty') from err
        except pd.errors.ParserError as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err

    def _create_workshop_from_tracks(self, tracks: List[WorkshopTrack]) -> Workshop:
        """Create Workshop object from tracks with validation."""
        try:
            return Workshop(tracks=tracks)
        except ValidationError as err:
            error_details = []
            for error in err.errors():
                field_path = ' -> '.join(str(loc) for loc in error['loc'])
                error_details.append(f"Field '{field_path}': {error['msg']}")
            raise ConfigurationError(
                f'Validation failed for workshop configuration:\n'
                f'  • {chr(10).join("  • " + detail for detail in error_details)}'
            ) from err
        except Exception as err:
            raise ConfigurationError(f'Unexpected error creating workshop from tracks: {err}') from err

    def load_workshop_tracks(self, file_path: Union[str, Path]) -> Workshop:
        """
        Load workshop tracks from CSV file and validate data.
        Args:
            file_path: Path to the workshop_tracks.csv file
        Returns:
            Workshop: Validated workshop configuration with tracks
        Raises:
            ConfigurationError: If file not found, CSV parsing fails, or validation fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ConfigurationError(f'Workshop tracks file not found: {file_path}')

        logger.info('Loading workshop tracks from %s', file_path)

        try:
            # Read and validate CSV data
            df = self._read_and_validate_workshop_tracks_csv(file_path)

            # Create WorkshopTrack objects
            tracks = self._create_workshop_tracks_from_dataframe(df)

            # Create Workshop with validation
            workshop = self._create_workshop_from_tracks(tracks)

            logger.info('Successfully loaded %d workshop tracks from %s', len(tracks), file_path)
            return workshop

        except ConfigurationError as err:
            raise err
        except Exception as err:
            raise ConfigurationError(f'Unexpected error loading workshop tracks from {file_path}: {err}') from err

    def _validate_scenario_dates(self, scenario_data: dict[str, Any]) -> tuple[date, date]:
        """Validate and convert scenario start/end dates."""
        scenario_start_str = scenario_data.get('start_date')
        scenario_end_str = scenario_data.get('end_date')

        if not scenario_start_str or not scenario_end_str:
            raise ConfigurationError('Missing start_date or end_date in scenario configuration')

        try:
            scenario_start = date.fromisoformat(scenario_start_str)
            scenario_end = date.fromisoformat(scenario_end_str)
            return scenario_start, scenario_end
        except ValueError as e:
            raise ConfigurationError(f'Invalid date format in scenario configuration: {e}') from e

    def _validate_train_dates_in_range(self, trains: List[Train], scenario_start: date, scenario_end: date) -> None:
        """Validate that all train arrivals fall within scenario date range."""
        out_of_range_trains = []
        for train in trains:
            if train.arrival_date < scenario_start or train.arrival_date > scenario_end:
                out_of_range_trains.append(f'{train.train_id} ({train.arrival_date})')

        if out_of_range_trains:
            raise ConfigurationError(
                f'Train arrivals outside scenario date range '
                f'({scenario_start} to {scenario_end}): '
                f'{", ".join(out_of_range_trains)}'
            )

    def _load_workshop_and_routes(self, config_dir: Path) -> tuple[Workshop, List]:
        """Load workshop tracks and routes configuration."""
        workshop_tracks_file = 'workshop_tracks.csv'
        workshop = self.load_workshop_tracks(config_dir / workshop_tracks_file)

        routes_file_name = 'routes.csv'
        routes_file = config_dir / routes_file_name
        routes_config = RoutesConfig(routes_file)
        routes = routes_config.routes

        return workshop, routes

    def _build_scenario_config(
        self,
        scenario_data: dict[str, Any],
        scenario_dates: tuple[date, date],
        components: tuple[str, Workshop, List[Train], List],  # train_schedule_file, workshop, trains, routes
    ) -> ScenarioConfig:
        """Build and validate ScenarioConfig object."""
        scenario_id = scenario_data.get('scenario_id')
        random_seed = scenario_data.get('random_seed')

        if not scenario_id:
            raise ConfigurationError('Missing scenario_id in scenario configuration')

        scenario_start, scenario_end = scenario_dates
        train_schedule_file, workshop, trains, routes = components
        return ScenarioConfig(
            scenario_id=scenario_id,
            start_date=scenario_start,
            end_date=scenario_end,
            random_seed=random_seed,
            train_schedule_file=train_schedule_file,
            workshop=workshop,
            train=trains,
            routes=routes,
        )

    def load_complete_scenario(self, path: Union[str, Path]) -> ScenarioConfig:
        """
        Load scenario configuration and train schedule data.
        Args:
            path: Directory path containing configuration files
        Returns:
            ScenarioConfig: Loaded and validated scenario configuration
        """
        scenario_data = self.load_and_validate_scenario(path)
        config_dir = Path(path) if isinstance(path, str) else path

        if config_dir.is_file():
            config_dir = config_dir.parent

        # 1. Load train schedule
        train_schedule_file = scenario_data.get('train_schedule_file')
        if not train_schedule_file:
            raise ConfigurationError('Missing train_schedule_file in scenario configuration')

        train_schedule_path = config_dir / train_schedule_file
        trains = self.load_train_schedule(train_schedule_path)

        # 2. Validate scenario dates and train arrivals
        scenario_dates = self._validate_scenario_dates(scenario_data)
        self._validate_train_dates_in_range(trains, scenario_dates[0], scenario_dates[1])

        # 3. Load workshop and routes configuration
        workshop, routes = self._load_workshop_and_routes(config_dir)

        # 4. Build ScenarioConfig
        components = (train_schedule_file, workshop, trains, routes)
        config = self._build_scenario_config(
            scenario_data=scenario_data,
            scenario_dates=scenario_dates,
            components=components,
        )

        logger.info('Successfully loaded complete scenario: %s', config.scenario_id)
        return config
