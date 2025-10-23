"""
Configuration service for loading, validating, and managing train simulation data.

This module provides the ConfigurationService class that handles:
- Loading and validating scenario configurations from JSON files
- Loading and parsing train schedule data from CSV files
- Creating validated domain models (ScenarioConfig, TrainArrival, WagonInfo)
- Cross-validation between scenario dates and train arrival dates
- Comprehensive error handling and logging for configuration issues
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd
from pydantic import ValidationError

from .model_scenario import ScenarioConfig
from .model_track import TrackFunction, WorkshopTrackConfig
from .model_train import TrainArrival
from .model_wagon import WagonInfo
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

    def load_scenario(self, path: Union[str, Path]) -> ScenarioConfig:
        """
        Load scenario configuration from a JSON file.
        Args:
            path: Directory path containing scenario.json or direct path to JSON file
        Returns:
            ScenarioConfig: Validated scenario configuration
        """
        path = Path(path)

        # Handle both directory and file paths
        if path.is_dir():
            file_path = path / 'scenario.json'
        elif path.suffix == '.json':
            file_path = path
        else:
            file_path = path / 'scenario.json'

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

            scenario_config = ScenarioConfig(**data)
            logger.info('Successfully loaded scenario: %s', scenario_config.scenario_id)
            return scenario_config

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

    def load_and_validate_scenario(self, path: Union[str, Path]) -> ScenarioConfig:
        """
        Load scenario configuration and validate all referenced files exist.
        Args:
            path: Directory path containing scenario.json
        Returns:
            ScenarioConfig: Validated scenario configuration
        """
        scenario_config = self.load_scenario(path)
        config_dir = Path(path) if isinstance(path, str) else path

        if config_dir.is_file():
            config_dir = config_dir.parent

        # Validate referenced files exist
        train_schedule_path = config_dir / scenario_config.train_schedule_file
        if not train_schedule_path.exists():
            raise ConfigurationError(f'Train schedule file not found: {train_schedule_path}')

        logger.info('All referenced files validated for scenario: %s', scenario_config.scenario_id)
        return scenario_config

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
        except (pd.errors.ParserError, TypeError) as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err
        if df.empty:
            raise ConfigurationError(f'Train schedule file is empty: {file_path}')
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
    def to_bool(value):
        """Robustly convert a value to boolean for CSV converters."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() == 'true'
        return False

    def _create_wagons_from_group(self, group: pd.DataFrame) -> List[WagonInfo]:
        """Create WagonInfo objects from a train group."""
        wagons = []
        for _, row in group.iterrows():
            try:
                wagon = WagonInfo(
                    wagon_id=str(row['wagon_id']),
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

    def _create_train_arrivals(self, df: pd.DataFrame) -> List[TrainArrival]:
        """Group by train and create TrainArrival objects."""
        # Parse time column
        try:
            df['arrival_time'] = pd.to_datetime(df['arrival_time'], format='%H:%M').dt.time
        except ValueError as err:
            raise ConfigurationError(f'Invalid time format in arrival_time. Expected HH:MM format: {err}') from err
        # Check for duplicate wagon IDs
        duplicate_wagons = df[df.duplicated(subset=['wagon_id'], keep=False)]['wagon_id'].unique()
        if len(duplicate_wagons) > 0:
            raise ConfigurationError(f'Duplicate wagon IDs found: {", ".join(duplicate_wagons)}')
        trains = []
        for train_id, group in df.groupby('train_id'):
            unique_dates = group['arrival_date'].nunique()
            unique_times = group['arrival_time'].nunique()
            if unique_dates > 1 or unique_times > 1:
                raise ConfigurationError(f'Train {train_id} has inconsistent arrival date/time across wagons')
            wagons = self._create_wagons_from_group(group)
            try:
                train_arrival = TrainArrival(
                    train_id=str(train_id),
                    arrival_date=group.iloc[0]['arrival_date'].date(),
                    arrival_time=group.iloc[0]['arrival_time'],
                    wagons=wagons,
                )
                trains.append(train_arrival)
            except ValidationError as err:
                error_details = []
                for error in err.errors():
                    field_path = ' -> '.join(str(loc) for loc in error['loc'])
                    error_details.append(f"Field '{field_path}': {error['msg']}")
                raise ConfigurationError(
                    f'Validation failed for train arrival {train_id}:\n'
                    f'  • {chr(10).join("  • " + detail for detail in error_details)}'
                ) from err
        return trains

    def load_train_schedule(self, file_path: Union[str, Path]) -> List[TrainArrival]:
        """
        Load train schedule from CSV file and validate data.
        Args:
            file_path: Path to the train schedule CSV file
        Returns:
            List[TrainArrival]: Validated train arrivals with wagon information
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

    def _create_workshop_tracks_from_dataframe(self, df: pd.DataFrame) -> List[WorkshopTrackConfig]:
        """Create WorkshopTrackConfig objects from DataFrame rows."""
        tracks = []
        for _, row in df.iterrows():
            try:
                track = WorkshopTrackConfig(
                    id=str(row['id']).strip(),
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
                    f'Validation failed for track {row["id"]}:\n'
                    f'  • {chr(10).join("  • " + detail for detail in error_details)}'
                ) from err
            except (ValueError, TypeError) as err:
                raise ConfigurationError(f'Invalid data type for track {row["id"]}: {err}') from err
        return tracks

    def _read_and_validate_workshop_tracks_csv(self, file_path: Path) -> pd.DataFrame:
        """Read and validate workshop tracks CSV file."""
        try:
            # Read CSV with appropriate data types
            df = pd.read_csv(file_path, dtype={'id': str, 'function': str, 'capacity': int, 'retrofit_time_min': int})

            # Check that the loaded object is a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                raise ConfigurationError(f'Loaded object is not a pandas DataFrame: got {type(df)}')

            if df.empty:
                raise ConfigurationError(f'Workshop tracks file is empty: {file_path}')

            # Validate required columns
            required_columns = ['id', 'function', 'capacity', 'retrofit_time_min']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ConfigurationError(
                    f'Missing required columns in {file_path}: '
                    f'{", ".join(missing_columns)}. Found columns: {", ".join(df.columns)}'
                )

            # Check for duplicate track IDs
            duplicate_ids = df[df.duplicated(subset=['id'], keep=False)]['id'].unique()
            if len(duplicate_ids) > 0:
                raise ConfigurationError(f'Duplicate track IDs found: {", ".join(duplicate_ids)}')

            return df

        except pd.errors.ParserError as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err

    def _create_workshop_from_tracks(self, tracks: List[WorkshopTrackConfig]) -> Workshop:
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

            # Create WorkshopTrackConfig objects
            tracks = self._create_workshop_tracks_from_dataframe(df)

            # Create Workshop with validation
            workshop = self._create_workshop_from_tracks(tracks)

            logger.info('Successfully loaded %d workshop tracks from %s', len(tracks), file_path)
            return workshop

        except ConfigurationError as err:
            raise err
        except Exception as err:
            raise ConfigurationError(f'Unexpected error loading workshop tracks from {file_path}: {err}') from err

    def load_complete_scenario(self, path: Union[str, Path]) -> tuple[ScenarioConfig, List[TrainArrival]]:
        """
        Load scenario configuration and train schedule data.
        Args:
            path: Directory path containing configuration files
        Returns:
            tuple: (ScenarioConfig, List of TrainArrival)
        """
        scenario_config = self.load_and_validate_scenario(path)
        config_dir = Path(path) if isinstance(path, str) else path

        if config_dir.is_file():
            config_dir = config_dir.parent

        train_schedule_path = config_dir / scenario_config.train_schedule_file
        train_arrivals = self.load_train_schedule(train_schedule_path)

        # Validate that train arrivals fall within scenario date range
        scenario_start = scenario_config.start_date
        scenario_end = scenario_config.end_date

        # Check each train arrival date against the scenario's valid date range
        out_of_range_trains = []
        for train in train_arrivals:
            # If train arrives before scenario starts or after scenario ends, it's invalid
            if train.arrival_date < scenario_start or train.arrival_date > scenario_end:
                # Collect train ID and arrival date for error reporting
                out_of_range_trains.append(f'{train.train_id} ({train.arrival_date})')

        # If any trains are outside the valid date range, raise an error with details
        if out_of_range_trains:
            raise ConfigurationError(
                f'Train arrivals outside scenario date range '
                f'({scenario_start} to {scenario_end}): '
                f'{", ".join(out_of_range_trains)}'
            )

        logger.info('Successfully loaded complete scenario: %s', scenario_config.scenario_id)
        return scenario_config, train_arrivals
