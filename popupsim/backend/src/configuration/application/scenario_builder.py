"""Configuration service for loading, validating, and managing train simulation data.

This module provides the ConfigurationService class that handles:
- Loading and validating scenario configurations from JSON files
- Loading and parsing train schedule data from CSV files
- Creating validated domain models (ScenarioConfig, Train, Wagon)
- Cross-validation between scenario dates and train arrival dates
- Comprehensive error handling and logging for models issues
"""

import json
import logging
from pathlib import Path

from configuration.domain.models.locomotive import Locomotive
from configuration.domain.models.process_times import ProcessTimes
from configuration.domain.models.routes import Routes
from configuration.domain.models.scenario import Scenario
from configuration.domain.models.topology import Topology
from configuration.domain.models.workshop import Workshop
from configuration.domain.services.scenario_validator import ScenarioValidator
from configuration.infrastructure.parsers.track_list_parser import TrackListParser
from configuration.infrastructure.parsers.train_list_parser import TrainListParser

# Configure logging
logger = logging.getLogger('ConfigurationService')

SCENARIOFILE = 'scenario.json'


# pylint: disable=too-few-public-methods
class BuilderError(Exception):
    """Custom exception for models-related errors."""


class ScenarioBuilder:
    """Service for loading and validating models files."""

    def __init__(self, scenario_path: Path):
        """Initialize the models service.

        Parameters
        ----------
        scenario_path : Path
            Directory for scenario files.
        """
        self.references: dict = {}
        self.scenario_path = scenario_path
        self.scenario: Scenario | None = None
        self.validator = ScenarioValidator()

    def __load_locomotives(self) -> None:
        """Load locomotives from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If locomotives file is not specified or loading fails.
        """
        locomotives_file: str | None = self.references.get('locomotives')

        if not locomotives_file:
            raise BuilderError('Missing locomotives file reference in scenario configuration')

        # Replace filename in scenario_path with locomotives_file
        scenario_dir: Path = Path(self.scenario_path).parent
        locomotives_path: Path = scenario_dir / locomotives_file

        if not locomotives_path.exists():
            raise BuilderError(f'Locomotives file not found: {locomotives_path}')

        try:
            if isinstance(self.scenario, Scenario):
                with locomotives_path.open('r') as f:
                    locomotive_data = json.load(f)

                locomotive_list: list[dict[str, str]] = locomotive_data.get('locomotives')
                self.scenario.locomotives = [Locomotive(**data) for data in locomotive_list]

        except json.JSONDecodeError as e:
            raise BuilderError(f'Invalid JSON format in {locomotives_path}: {e!s}') from e
        except Exception as e:
            raise BuilderError(f'Failed to load locomotives from {locomotives_path}: {e!s}') from e

    def __load_routes(self) -> None:
        """Load routes from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If routes file is not specified or loading fails.
        """
        routes_file: str | None = self.references.get('routes')

        if not routes_file:
            raise BuilderError('Missing routes file reference in scenario configuration')

        # Replace filename in scenario_path with routes_file
        scenario_dir: Path = Path(self.scenario_path).parent
        routes_path: Path = scenario_dir / routes_file

        if not routes_path.exists():
            raise BuilderError(f'Routes file not found: {routes_path}')

        try:
            if isinstance(self.scenario, Scenario):
                self.scenario.routes = Routes(routes_path).routes

        except Exception as e:
            raise BuilderError(f'Failed to load routes from {routes_path}: {e!s}') from e

    def __load_topology(self) -> None:
        """Load topology from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If topology file is not specified or loading fails.
        """
        topology_file: str | None = self.references.get('topology')

        if not topology_file:
            raise BuilderError('Missing topology file reference in scenario configuration')

        scenario_dir: Path = Path(self.scenario_path).parent
        topology_path: Path = scenario_dir / topology_file

        if not topology_path.exists():
            raise BuilderError(f'Topology file not found: {topology_path}')

        try:
            if isinstance(self.scenario, Scenario):
                self.scenario.topology = Topology(topology_path)

        except Exception as e:
            raise BuilderError(f'Failed to load topology from {topology_path}: {e!s}') from e

    def __load_process_times(self) -> None:
        """Load process times from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If process times file is not specified or loading fails.
        """
        process_times_file: str | None = self.references.get('process_times')

        if not process_times_file:
            raise BuilderError('Missing process_times file reference in scenario configuration')

        scenario_dir: Path = Path(self.scenario_path).parent
        process_times_path: Path = scenario_dir / process_times_file

        if not process_times_path.exists():
            raise BuilderError(f'Process times file not found: {process_times_path}')

        try:
            if isinstance(self.scenario, Scenario):
                self.scenario.process_times = ProcessTimes.load_from_file(process_times_path)

        except Exception as e:
            raise BuilderError(f'Failed to load process times from {process_times_path}: {e!s}') from e

    def __load_scenario(self) -> None:
        """Load scenario models from a JSON file.

        Parameters
        ----------
        path : str | Path
            Directory path containing scenario.json or direct path to JSON file.

        Returns
        -------
        None

        """
        logger.info('Loading scenario models from %s', self.scenario_path)

        try:
            with open(self.scenario_path, encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields exist before creating model
            required_fields = ['scenario_id', 'start_date', 'end_date', 'references']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise BuilderError(
                    f'Missing required fields {", ".join(missing_fields)} in {self.scenario_path}: '
                    f'Found fields: {", ".join(data.keys())}'
                )

            self.scenario = Scenario(**data)
            self.references = data.get('references', {})

            logger.info('Successfully loaded scenario: %s', data.get('scenario_id'))

        except json.JSONDecodeError as e:
            error_msg = (
                f'Invalid JSON syntax in {self.scenario_path} at line {e.lineno}, column {e.colno}: {e.msg}. '
                'Please check the JSON structure and ensure all brackets and quotes are properly closed.'
            )
            logger.error('%s', error_msg)
            raise BuilderError(error_msg) from e
        except Exception as e:
            error_msg = f'Error loading scenario models from {self.scenario_path}: {e}'
            logger.error('%s', error_msg)
            raise BuilderError(error_msg) from e

    def __load_tracks(self) -> None:
        """Load tracks from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If tracks file is not specified or loading fails.
        """
        tracks_file: str | None = self.references.get('tracks')

        if not tracks_file:
            raise BuilderError('Missing tracks file reference in scenario configuration')

        # Replace filename in scenario_path with tracks_file
        scenario_dir: Path = Path(self.scenario_path).parent
        tracks_path: Path = scenario_dir / tracks_file

        if not tracks_path.exists():
            raise BuilderError(f'Tracks file not found: {tracks_path}')

        try:
            if isinstance(self.scenario, Scenario):
                self.scenario.tracks = TrackListParser(tracks_path).build()

        except Exception as e:
            raise BuilderError(f'Failed to load tracks from {tracks_path}: {e!s}') from e

    def __load_trains(self) -> None:
        """Load trains from CSV file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If trains file is not specified or loading fails.
        """
        trains_file: str | None = self.references.get('trains')

        if not trains_file:
            raise BuilderError('Missing trains file reference in scenario configuration')

        # Replace filename in scenario_path with trains_file
        scenario_dir: Path = Path(self.scenario_path).parent
        trains_path: Path = scenario_dir / trains_file

        if not trains_path.exists():
            raise BuilderError(f'Trains file not found: {trains_path}')

        try:
            if isinstance(self.scenario, Scenario):
                self.scenario.trains = TrainListParser(trains_path).build()

        except Exception as e:
            raise BuilderError(f'Failed to load trains from {trains_path}: {e!s}') from e

    def __load_workshops(self) -> None:
        """Load workshops from JSON file referenced in scenario configuration.

        Raises
        ------
        BuilderError
            If workshops file is not specified or loading fails.
        """
        workshops_file: str | None = self.references.get('workshops')

        if not workshops_file:
            raise BuilderError('Missing workshops file reference in scenario configuration')

        # Replace filename in scenario_path with workshops_file
        scenario_dir: Path = Path(self.scenario_path).parent
        workshops_path: Path = scenario_dir / workshops_file

        if not workshops_path.exists():
            raise BuilderError(f'Workshops file not found: {workshops_path}')

        try:
            if isinstance(self.scenario, Scenario):
                with open(workshops_path, encoding='utf-8') as f:
                    workshops_data: dict[str, object] = json.load(f)

                if 'workshops' not in workshops_data:
                    raise BuilderError(f'No workshops found in {workshops_path}')

                workshops_list: list[dict[str, object]] = workshops_data['workshops']  # type: ignore[assignment]
                self.scenario.workshops = [Workshop(**data) for data in workshops_list]  # type: ignore[arg-type]

        except json.JSONDecodeError as e:
            raise BuilderError(f'Invalid JSON format in {workshops_path}: {e!s}') from e
        except Exception as e:
            raise BuilderError(f'Failed to load workshops from {workshops_path}: {e!s}') from e

    def __find_scenario_in_path(self, path: Path) -> None:
        # Handle both directory and file paths
        if path.is_dir():
            # First try scenario.json for test fixtures, then fallback to scenario.json
            test_file_path = path / SCENARIOFILE
            file_path = test_file_path if test_file_path.exists() else path / SCENARIOFILE
        elif path.suffix == '.json':
            file_path = path
        else:
            # First try scenario.json for test fixtures, then fallback to scenario.json
            test_file_path = path / SCENARIOFILE
            file_path = test_file_path if test_file_path.exists() else path / SCENARIOFILE

        if not file_path.exists():
            raise BuilderError(f'Scenario models file not found: {file_path}')

        self.scenario_path = file_path

    def build(self) -> Scenario:
        """Build and return the scenario models.

        Returns
        -------
        Scenario
            Loaded scenario models.

        Raises
        ------
        BuilderError
            If loading or validation fails.
        """
        path = Path(self.scenario_path)

        self.__find_scenario_in_path(path)
        self.__load_scenario()
        if isinstance(self.scenario, Scenario):
            self.__load_locomotives()
            self.__load_tracks()
            self.__load_trains()
            self.__load_routes()
            self.__load_topology()
            self.__load_process_times()
            self.__load_workshops()
            # Validate scenario after all referenced files are loaded
            self.scenario.validate_simulation_requirements()
        else:
            raise BuilderError('Scenario could not be loaded properly.')
        return self.scenario
