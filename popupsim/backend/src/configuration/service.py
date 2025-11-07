"""Configuration service for loading, validating, and managing train simulation data.

This module provides the ConfigurationService class that handles:
- Loading and validating scenario configurations from JSON files
- Loading and parsing train schedule data from CSV files
- Creating validated domain models (ScenarioConfig, Train, Wagon)
- Cross-validation between scenario dates and train arrival dates
- Comprehensive error handling and logging for configuration issues
"""

from datetime import UTC
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from .model_routes import Route
from .model_routes import Routes
from .model_scenario import ScenarioConfig
from .model_track import Track
from .model_track import TrackType
from .model_train import Train
from .model_wagon import Wagon
from .validation import ConfigurationValidator

# Configure logging
logger = logging.getLogger('ConfigurationService')


# pylint: disable=too-few-public-methods
class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


class ConfigurationService:
    """Service for loading and validating configuration files."""

    def __init__(self, base_path: Path | None = None):
        """Initialize the configuration service.

        Parameters
        ----------
        base_path : Path | None, optional
            Base directory for configuration files, by default None (uses current directory).
            # Todo Clarify why we need that
        """
        self.base_path = base_path or Path.cwd()
        self.validator = ConfigurationValidator()

    def load_scenario(self, path: str | Path) -> dict[str, Any]:
        """Load scenario configuration from a JSON file.

        Parameters
        ----------
        path : str | Path
            Directory path containing scenario.json or direct path to JSON file.

        Returns
        -------
        dict[str, Any]
            Scenario configuration data.

        Raises
        ------
        ConfigurationError
            If file not found, JSON is invalid, or required fields are missing.
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
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields exist before creating model
            required_fields = ['scenario_id', 'start_date', 'end_date', 'train_schedule_file']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ConfigurationError(
                    f'Missing required fields {", ".join(missing_fields)} in {file_path}: '
                    f'Found fields: {", ".join(data.keys())}'
                )

            logger.info('Successfully loaded scenario: %s', data.get('scenario_id'))
            return data  # type: ignore[no-any-return]

        except json.JSONDecodeError as e:
            error_msg = (
                f'Invalid JSON syntax in {file_path} at line {e.lineno}, column {e.colno}: {e.msg}. '
                'Please check the JSON structure and ensure all brackets and quotes are properly closed.'
            )
            logger.error('%s', error_msg)
            raise ConfigurationError(error_msg) from e

    def load_and_validate_scenario_data(self, path: str | Path) -> dict[str, Any]:
        """Load scenario configuration and validate all referenced files exist.

        Parameters
        ----------
        path : str | Path
            Directory path containing scenario.json.

        Returns
        -------
        dict[str, Any]
            Validated scenario configuration data.

        Raises
        ------
        ConfigurationError
            If scenario loading fails or referenced files don't exist.
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

    def load_scenario_config(self, path: str | Path) -> ScenarioConfig:
        """Load and validate scenario configuration from a JSON file.

        Parameters
        ----------
        path : str | Path
            Directory path containing scenario.json or direct path to JSON file.

        Returns
        -------
        ScenarioConfig
            Validated ScenarioConfig object.

        Raises
        ------
        ConfigurationError
            If loading or validation fails.
        """
        data = self.load_and_validate_scenario_data(path)
        try:
            scenario = ScenarioConfig(**data)
            logger.info('ScenarioConfig created successfully for: %s', scenario.scenario_id)
            return scenario
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field_path = ' -> '.join(str(loc) for loc in error['loc'])
                error_details.append(f"Field '{field_path}': {error['msg']} (input: {error.get('input', 'N/A')})")
            error_msg = (
                f'Validation failed for scenario configuration in {path}:\n'
                f'  • {chr(10).join("  • " + detail for detail in error_details)}'
            )
            logger.error('%s', error_msg)
            raise ConfigurationError(error_msg) from e

    def _read_and_validate_train_schedule_csv(self, file_path: Path) -> pd.DataFrame:
        """Read CSV and validate required columns and emptiness.

        Parameters
        ----------
        file_path : Path
            Path to the CSV file to read.

        Returns
        -------
        pd.DataFrame
            Validated DataFrame with train schedule data.

        Raises
        ------
        ConfigurationError
            If file is empty, has parsing errors, or missing required columns.
        """
        try:
            df = pd.read_csv(
                file_path,
                sep=';',
                dtype={'train_id': str, 'wagon_id': str},
                parse_dates=['arrival_time'],
                date_format={'arrival_time': '%Y-%m-%d %H:%M'},
            )
            # Replace empty train_id with "AnoTrain"
            df['train_id'] = df['train_id'].fillna('AnoTrain')
            df.loc[df['train_id'].str.strip() == '', 'train_id'] = 'AnoTrain'
            if len(df) < 1:
                raise ConfigurationError('Train schedule file is empty')
        except (pd.errors.ParserError, TypeError) as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err
        except Exception as err:
            # ToDo avoid unexpected ! Files can be empty, have missing columns, wrong formats, ...
            raise ConfigurationError(f'Unexpected error reading CSV file {file_path}: {err}') from err

        if df.empty:
            raise ConfigurationError('Train schedule file is empty')
        required_columns = [
            'train_id',
            'wagon_id',
            'length',
            'selector',
            'arrival_time',
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

    def _create_wagons_from_group(self, group: pd.DataFrame) -> list[Wagon]:
        """Create Wagon objects from a DataFrame group.

        Parameters
        ----------
        group : pd.DataFrame
            DataFrame containing wagon data for a single train.

        Returns
        -------
        list[Wagon]
            List of validated Wagon objects.

        Raises
        ------
        ValidationError
            If wagon validation fails.
        """
        wagons: list[Wagon] = []

        for _, row in group.iterrows():
            try:
                wagon: Wagon = Wagon(
                    wagon_id=str(row['wagon_id']),
                    train_id=str(row['train_id']),
                    length=float(row['length']),
                    is_loaded=self._to_bool(row['is_loaded']),
                    needs_retrofit=self._to_bool(row['needs_retrofit']),
                    arrival_time=None,  # Set later if needed
                    retrofit_start_time=None,
                    retrofit_end_time=None,
                    track_id=None,
                )
                wagons.append(wagon)
            except ValidationError as err:
                logger.error('Failed to create wagon %s for train %s: %s', row['wagon_id'], row['train_id'], err)
                raise

        return wagons

    def _create_trains_from_dataframe(self, df: pd.DataFrame) -> list[Train]:
        """Create Train objects from DataFrame grouped by train_id.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with all train schedule data.

        Returns
        -------
        list[Train]
            List of validated Train objects with their wagons.

        Raises
        ------
        ConfigurationError
            If train creation or validation fails.
        """
        trains: list[Train] = []

        # Group by train_id to process each train's wagons together
        grouped: pd.core.groupby.DataFrameGroupBy = df.groupby('train_id')

        for train_id, group_df in grouped:
            try:
                # Get first row for train-level data (all rows have same arrival_time per train)
                first_row: pd.Series[Any] = group_df.iloc[0]

                # Parse arrival_time from pd.Timestamp to datetime with UTC timezone
                arrival_timestamp: pd.Timestamp = first_row['arrival_time']
                arrival_datetime: datetime = datetime.strptime(str(arrival_timestamp), '%Y-%m-%d %H:%M:%S').replace(
                    tzinfo=UTC
                )
                # Create wagons for this train
                wagons: list[Wagon] = self._create_wagons_from_group(group_df)

                # Create Train object
                train: Train = Train(
                    train_id=str(train_id),
                    arrival_time=arrival_datetime,  # Pass datetime, not time
                    wagons=wagons,
                )
                trains.append(train)

                logger.debug(
                    'Created train %s with %d wagons, arrival time: %s', train_id, len(wagons), arrival_datetime
                )

            except ValidationError as err:
                error_msg: str = f'Failed to create train {train_id}: {err}'
                logger.error(error_msg)
                raise ConfigurationError(error_msg) from err
            except Exception as err:
                error_msg = f'Unexpected error creating train {train_id}: {err}'
                logger.error(error_msg)
                raise ConfigurationError(error_msg) from err

        logger.info('Successfully created %d trains from DataFrame', len(trains))
        return trains

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Convert various representations to boolean.

        Parameters
        ----------
        value : Any
            Value to convert (string, bool, int).

        Returns
        -------
        bool
            Converted boolean value.

        Raises
        ------
        ValueError
            If value cannot be converted to boolean.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value_lower: str = value.lower().strip()
            if value_lower in ('true', '1', 'yes', 'y'):
                return True
            if value_lower in ('false', '0', 'no', 'n'):
                return False
            raise ValueError(f'Cannot convert string "{value}" to boolean')
        if isinstance(value, int):
            return bool(value)
        raise ValueError(f'Cannot convert {type(value).__name__} to boolean')

    def load_train_schedule(self, file_path: str | Path) -> list[Train]:
        """Load train schedule from CSV file and validate data.

        Parameters
        ----------
        file_path : str | Path
            Path to the train schedule CSV file.

        Returns
        -------
        list[Train]
            List of validated Train objects with their wagons.

        Raises
        ------
        ConfigurationError
            If file not found, CSV parsing fails, or validation fails.
        """
        file_path_obj: Path = Path(file_path)
        if not file_path_obj.exists():
            raise ConfigurationError(f'Train schedule file not found: {file_path_obj}')

        logger.info('Loading train schedule from %s', file_path_obj)

        try:
            # Read and validate CSV
            df: pd.DataFrame = self._read_and_validate_train_schedule_csv(file_path_obj)

            # Create Train objects from DataFrame
            trains: list[Train] = self._create_trains_from_dataframe(df)

            # Log summary
            total_wagons: int = sum(len(train.wagons) for train in trains)
            logger.info(
                'Successfully loaded %d trains with %d total wagons from %s', len(trains), total_wagons, file_path_obj
            )
            return trains

        except Exception as err:
            raise ConfigurationError(f'Unexpected error loading train schedule from {file_path_obj}: {err}') from err

    def _create_workshop_tracks_from_dataframe(self, df: pd.DataFrame) -> list[Track]:
        """Create WorkshopTrack objects from DataFrame rows."""
        tracks = []
        for _, row in df.iterrows():
            try:
                capacity = self._extract_scalar_int(row['capacity'])

                track = Track(
                    id=str(row['track_id']).strip(),
                    length=float(row['length']),
                    type=TrackType(str(row['function']).strip()),
                    capacity=capacity,
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

    def _parse_current_wagons(self, row: pd.Series, df: pd.DataFrame) -> list[int]:
        """Parse current_wagons field from DataFrame row."""
        current_wagons: list[int] = []
        if 'current_wagons' in df.columns and pd.notna(row['current_wagons']):
            current_wagons_val = row['current_wagons']
            # Extract scalar value if needed
            if not pd.api.types.is_scalar(current_wagons_val):
                current_wagons_val = current_wagons_val.iloc[0]

            # Parse the current_wagons value
            if isinstance(current_wagons_val, str):
                # Handle comma-separated string of wagon IDs
                current_wagons_str = current_wagons_val.strip()
                if current_wagons_str:
                    current_wagons = [int(wagon_id.strip()) for wagon_id in current_wagons_str.split(',')]
            elif isinstance(current_wagons_val, (int, float)):
                # Handle single wagon ID as integer
                current_wagons = [int(current_wagons_val)]
        return current_wagons

    def _extract_scalar_int(self, value: Any) -> int:
        """Extract scalar integer value from pandas Series or scalar."""
        return int(value) if pd.api.types.is_scalar(value) else int(value.iloc[0])

    def _read_and_validate_workshop_tracks_csv(self, file_path: Path) -> pd.DataFrame:
        """Read and validate workshop tracks CSV file."""
        try:
            # Read CSV with appropriate data types - expect track_id column
            df = pd.read_csv(
                file_path,
                dtype={
                    'track_id': str,
                    'function': str,
                    'capacity': int,
                    'retrofit_time_min': int,
                    'current_wagons': str,  # List of wagons as string parsed later will be List[int]
                },
            )
        except pd.errors.EmptyDataError as err:
            raise ConfigurationError('Workshop tracks file is empty') from err
        except pd.errors.ParserError as err:
            raise ConfigurationError(f'Error parsing CSV file {file_path}: {err}') from err

        # Validate that the result is actually a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise ConfigurationError('Loaded object is not a pandas DataFrame')

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

    def _load_tracks(self, file_path: Path) -> list[Track]:
        """Load track configuration from CSV file.

        Parameters
        ----------
        file_path : Path
            Path to the tracks CSV file.

        Returns
        -------
        list[Track]
            List of validated Track objects.

        Raises
        ------
        ConfigurationError
            If file not found, CSV parsing fails, or validation fails.
        """
        try:
            df: pd.DataFrame = pd.read_csv(
                file_path,
                sep=';',
                dtype={
                    'track_id': str,
                    'length': float,
                    'type': str,
                    'capacity': 'Int64',  # Nullable integer type
                    'sh_1': 'Int64',  # Nullable integer type
                    'sh_n': 'Int64',  # Nullable integer type
                    'valid_from': str,
                    'valid_to': str,
                },
                keep_default_na=True,
            )

            # Parse dates with error handling
            df['valid_from'] = pd.to_datetime(df['valid_from'], errors='coerce')
            df['valid_to'] = pd.to_datetime(df['valid_to'], errors='coerce')
            if df.empty:
                raise ConfigurationError(f'Track configuration file is empty: {file_path}')

            # Validate required columns
            required_columns: list[str] = ['id', 'length', 'type']
            missing_columns: list[str] = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ConfigurationError(f'Missing columns in {file_path}: {", ".join(missing_columns)}')

            # Convert DataFrame to Track objects
            tracks: list[Track] = []
            for _, row in df.iterrows():
                try:
                    track: Track = Track(
                        id=str(row['id']).strip(),
                        length=float(row['length']),
                        type=TrackType(str(row['type']).strip()),
                        capacity=int(row['capacity']) if pd.notna(row.get('capacity')) else None,
                        sh_1=int(row['sh_1']) if pd.notna(row.get('sh_1')) else 0,
                        sh_n=int(row['sh_n']) if pd.notna(row.get('sh_n')) else 0,
                        valid_from=row['valid_from'].to_pydatetime() if pd.notna(row.get('valid_from')) else None,
                        valid_to=row['valid_to'].to_pydatetime() if pd.notna(row.get('valid_to')) else None,
                    )
                    tracks.append(track)
                except ValidationError as err:
                    error_details: str = '; '.join(
                        f'{".".join(str(loc) for loc in e["loc"])}: {e["msg"]}' for e in err.errors()
                    )
                    raise ConfigurationError(f'Invalid track {row["track_id"]}: {error_details}') from err

            logger.info('Loaded %d tracks from %s', len(tracks), file_path)
            return tracks

        except Exception as err:
            raise ConfigurationError(f'File not found: {file_path}') from err

    # Todo Workshop handling
    # def load_workshop_tracks(self, file_path: str | Path) -> Workshop:
    #     """Load workshop tracks from CSV file and validate data.

    #     Parameters
    #     ----------
    #     file_path : str | Path
    #         Path to the workshop_tracks.csv file.

    #     Returns
    #     -------
    #     Workshop
    #         Validated workshop configuration with tracks.

    #     Raises
    #     ------
    #     ConfigurationError
    #         If file not found, CSV parsing fails, or validation fails.
    #     """
    #     file_path = Path(file_path)
    #     if not file_path.exists():
    #         raise ConfigurationError(f'Workshop tracks file not found: {file_path}')

    #     logger.info('Loading workshop tracks from %s', file_path)

    #     try:
    #         # Read and validate CSV data
    #         df = self._read_and_validate_workshop_tracks_csv(file_path)

    #         # Create WorkshopTrack objects
    #         tracks = self._create_workshop_tracks_from_dataframe(df)

    #         # Create Workshop with validation
    #         workshop = self._create_workshop_from_tracks(tracks)

    #         logger.info('Successfully loaded %d workshop tracks from %s', len(tracks), file_path)
    #         return workshop

    #     except ConfigurationError as err:
    #         raise err
    #     except Exception as err:
    #         raise ConfigurationError(f'Unexpected error loading workshop tracks from {file_path}: {err}') from err

    def _validate_scenario_dates(self, scenario_data: dict[str, Any]) -> tuple[datetime, datetime]:
        """Validate and convert scenario start/end dates to UTC timezone-aware datetimes.

        Parameters
        ----------
        scenario_data : dict[str, Any]
            Scenario configuration dictionary.

        Returns
        -------
        tuple[datetime, datetime]
            Start and end datetime with UTC timezone.

        Raises
        ------
        ConfigurationError
            If dates are missing or have invalid format.
        """
        scenario_start_str = scenario_data.get('start_date')
        scenario_end_str = scenario_data.get('end_date')

        if not scenario_start_str or not scenario_end_str:
            raise ConfigurationError('Missing start_date or end_date in scenario configuration')

        try:
            scenario_start = datetime.fromisoformat(scenario_start_str)
            scenario_end = datetime.fromisoformat(scenario_end_str)

            # Ensure both datetimes are timezone-aware (UTC)
            if scenario_start.tzinfo is None:
                scenario_start = scenario_start.replace(tzinfo=UTC)
            if scenario_end.tzinfo is None:
                scenario_end = scenario_end.replace(tzinfo=UTC)

            return scenario_start, scenario_end
        except ValueError as e:
            raise ConfigurationError(f'Invalid date format in scenario configuration: {e}') from e

    def _validate_train_dates_in_range(
        self, trains: list[Train], scenario_start: datetime, scenario_end: datetime
    ) -> list[Train]:
        """Validate train arrivals and filter out those outside scenario date range.

        Parameters
        ----------
        trains : list[Train]
            List of Train objects to validate.
        scenario_start : date
            Scenario start date.
        scenario_end : date
            Scenario end date.

        Returns
        -------
        list[Train]
            Filtered list containing only trains within scenario date range.
        """
        out_of_range_trains: list[str] = []
        valid_trains: list[Train] = []

        for train in trains:
            if train.arrival_time < scenario_start or train.arrival_time > scenario_end:
                out_of_range_trains.append(f'{train.train_id} ({train.arrival_time})')
            else:
                valid_trains.append(train)

        if out_of_range_trains:
            info: str = (
                f'Filtered out {len(out_of_range_trains)} train(s) with arrivals outside scenario date range '
                f'({scenario_start} to {scenario_end}): {", ".join(out_of_range_trains)}'
            )
            logger.warning('%s', info)

        logger.info(
            'Train validation complete: %d valid trains, %d filtered out', len(valid_trains), len(out_of_range_trains)
        )

        return valid_trains

    # def _load_workshop_and_routes(
    #     self, config_dir: Path, tracks_file: str | None, routes_file: str | None
    # ) -> tuple[Workshop, list]:
    #     """Load workshop tracks and routes configuration."""
    #     tracks_filename = tracks_file or 'workshop_tracks.csv'
    #     #workshop = self.load_workshop_tracks(config_dir / tracks_filename)
    #     routes_filename = routes_file or 'routes.csv'
    #     routes_path = config_dir / routes_filename
    #     routes_config = Routes(routes_path)
    #     routes = routes_config.routes

    #     return workshop, routes

    def _build_scenario_config(
        self,
        scenario_data: dict[str, Any],
        scenario_dates: tuple[datetime, datetime],
        train_schedule_file: str,  # Todo make it a path
        components: dict[str, Any],
    ) -> ScenarioConfig:
        """Build and validate ScenarioConfig object."""
        scenario_id = scenario_data.get('scenario_id')
        random_seed = scenario_data.get('random_seed')

        if not scenario_id:
            raise ConfigurationError('Missing scenario_id in scenario configuration')

        scenario_start, scenario_end = scenario_dates
        # Todo add Workshops
        return ScenarioConfig(
            scenario_id=scenario_id,
            start_date=scenario_start,
            end_date=scenario_end,
            random_seed=random_seed,
            routes=components.get('routes'),
            train_schedule_file=train_schedule_file,
            trains=components.get('trains'),
            tracks=components.get('tracks'),
        )

    def load_complete_scenario(self, path: str | Path) -> ScenarioConfig:
        """Load scenario configuration and train schedule data.

        Parameters
        ----------
        path : str | Path
            Directory path containing configuration files.

        Returns
        -------
        tuple[ScenarioConfig, ValidationResult]
            Loaded and validated scenario configuration with validation results.

        Raises
        ------
        ConfigurationError
            If loading or validation fails.
        """
        scenario_data: dict[str, Any] = self.load_and_validate_scenario_data(path)
        config_dir: Path = Path(path) if isinstance(path, str) else path

        if config_dir.is_file():
            config_dir = config_dir.parent

        # 1. Load train schedule
        train_schedule_file = scenario_data.get('train_schedule_file')
        if not train_schedule_file:
            raise ConfigurationError('Missing train_schedule_file in scenario configuration')

        train_schedule_path: Path = config_dir / train_schedule_file
        trains: list[Train] = self.load_train_schedule(train_schedule_path)

        # 2. Validate scenario dates and filter trains by arrival date
        scenario_dates: tuple[datetime, datetime] = self._validate_scenario_dates(scenario_data)
        trains = self._validate_train_dates_in_range(trains, scenario_dates[0], scenario_dates[1])

        # load tracks
        tracks_path = config_dir / scenario_data.get('tracks_file', 'tracks.csv')
        tracks: list[Track] = self._load_tracks(tracks_path)

        # Load routes if specified
        # Todo use only routes eithere here or in sim to hanlde occupation
        routes: list[Route] = []
        routes_file_name: str | None = scenario_data.get('routes_file')
        if routes_file_name:
            routes_path: Path = config_dir / routes_file_name
            if routes_path.exists():
                routes_config: Routes = Routes(routes_path)
                routes = routes_config.routes
                logger.info('Loaded %d routes from %s', len(routes), routes_path)
            else:
                logger.warning('Routes file specified but not found: %s', routes_path)
        else:
            logger.info('No routes file specified in scenario configuration')

        # 4. Build Scenario
        componenents = {
            'routes': routes,
            'trains': trains,
            'tracks': tracks,
        }
        scenario: ScenarioConfig = self._build_scenario_config(
            scenario_data=scenario_data,
            scenario_dates=scenario_dates,
            train_schedule_file=train_schedule_file,
            components=componenents,
        )

        logger.info('Successfully loaded complete scenario: %s', scenario.scenario_id)

        # 5. Validate configuration
        # Todo enable validations
        # logger.info('Starting configuration validation for scenario: %s', scenario.scenario_id)
        # validation_result: ValidationResult = self.validator.validate(scenario)

        # 6. Output validation results
        # logger.info(
        #     'Configuration validation completed for scenario: %s. Valid: %s, Errors: %d, Warnings: %d',
        #     scenario.scenario_id,
        #     validation_result.is_valid,
        #     len(validation_result.get_errors()),
        #     len(validation_result.get_warnings()),
        # )
        # validation_result.print_summary()

        return scenario
