"""
Configuration service for loading and validating scenario configurations and workshop track data.

This module provides functionality to:
- Load and validate scenario configurations from JSON files.
- Load and validate workshop track data from CSV files.
- Use Pydantic models for schema validation and error handling.
- Ensure data integrity and consistency through custom validation logic.

Key Features:
- Scenario configuration validation includes checks for date ranges, random seeds, and file references.
- Train schedule validation ensures proper structure, required fields, and data consistency.
- Custom exceptions (`ConfigurationError`) are used for error handling.
"""

import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

# Configure logging
logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


class WagonInfo(BaseModel):
    """Information about a single wagon."""

    wagon_id: str = Field(description='Unique identifier for the wagon')
    length: float = Field(gt=0, description='Length of the wagon in meters')
    is_loaded: bool = Field(description='Whether the wagon is loaded')
    needs_retrofit: bool = Field(description='Whether the wagon needs retrofit')


class TrainArrival(BaseModel):
    """Information about a train arrival with its wagons."""

    train_id: str = Field(description='Unique identifier for the train')
    arrival_date: date = Field(description='Date of arrival')
    arrival_time: time = Field(description='Time of arrival')
    wagons: List[WagonInfo] = Field(description='List of wagons in the train')

    @property
    def arrival_datetime(self) -> datetime:
        """Combined arrival date and time."""
        return datetime.combine(self.arrival_date, self.arrival_time)

    @model_validator(mode='after')
    def validate_wagons(self) -> 'TrainArrival':
        """Ensure train has at least one wagon."""
        if not self.wagons:
            raise ValueError(f'Train {self.train_id} must have at least one wagon')
        return self


class ScenarioConfig(BaseModel):
    """
    Configuration model for simulation scenarios.

    Validates scenario parameters including date ranges, random seeds,
    and required file references.
    """

    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$', description='Unique identifier for the scenario', min_length=1, max_length=50
    )
    start_date: date = Field(description='Simulation start date')
    end_date: date = Field(description='Simulation end date')
    random_seed: Optional[int] = Field(default=None, ge=0, description='Random seed for reproducible simulations')
    train_schedule_file: str = Field(description='Path to the train schedule file', min_length=1)

    @field_validator('train_schedule_file')
    @classmethod
    def validate_train_schedule_file(cls, v: str) -> str:
        """Validate that the train schedule file has a valid extension."""
        if not v.endswith(('.json', '.csv', '.xlsx')):
            raise ValueError(
                f"Invalid file extension for train_schedule_file: '{v}'. Expected one of: .json, .csv, .xlsx"
            )
        return v

    # mode="after" gives you the constructed instance (self),
    # so you can safely compare self.end_date and self.start_date.
    @model_validator(mode='after')
    def validate_dates(self) -> 'ScenarioConfig':
        """Ensure end_date is after start_date and duration is reasonable."""
        if self.end_date <= self.start_date:
            raise ValueError(
                f'Invalid date range: end_date ({self.end_date}) must be after start_date ({self.start_date}).'
            )
        duration = (self.end_date - self.start_date).days

        if duration > 365:
            logger.warning(
                "Simulation duration of %d days for scenario '%s' may impact performance.", duration, self.scenario_id
            )
        elif duration < 1:
            raise ValueError(f'Simulation duration must be at least 1 day. Current duration: {duration} days.')
        return self


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

    def _read_and_validate_csv(self, file_path: Path) -> pd.DataFrame:
        """Read CSV and validate required columns and emptiness."""
        try:
            df = pd.read_csv(
                file_path,
                dtype={
                    'train_id': str,
                    'wagon_id': str,
                    'length': float,
                    'is_loaded': bool,
                    'needs_retrofit': bool,
                },
                parse_dates=['arrival_date'],
                date_format='%Y-%m-%d',
            )
        except pd.errors.EmptyDataError as err:
            raise ConfigurationError(f'Train schedule file is empty or invalid: {file_path}') from err
        except pd.errors.ParserError as err:
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
        return df

    def _create_wagons_from_group(self, group: pd.DataFrame) -> List[WagonInfo]:
        """Create WagonInfo objects from a train group."""
        wagons = []
        for _, row in group.iterrows():
            try:
                wagon = WagonInfo(
                    wagon_id=row['wagon_id'],
                    length=row['length'],
                    is_loaded=row['is_loaded'],
                    needs_retrofit=row['needs_retrofit'],
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
            df = self._read_and_validate_csv(file_path)
            trains = self._create_train_arrivals(df)
            logger.info('Successfully loaded %d trains with %d wagons from %s', len(trains), len(df), file_path)
            return trains
        except ConfigurationError as err:
            raise err
        except Exception as err:
            raise ConfigurationError(f'Unexpected error loading train schedule from {file_path}: {err}') from err

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
