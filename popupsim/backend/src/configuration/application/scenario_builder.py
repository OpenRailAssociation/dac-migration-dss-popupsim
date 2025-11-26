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
from typing import Any

from configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from configuration.application.dtos.route_input_dto import RouteInputDTO
from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO
from configuration.application.dtos.track_input_dto import TrackInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO

from configuration.domain.models.process_times import ProcessTimes
from configuration.domain.models.scenario import Scenario
from configuration.domain.models.topology import Topology
from configuration.domain.services.scenario_validator import ScenarioValidator


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
        self.scenario_path = scenario_path
        self.scenario: Scenario | None = None
        self.validator = ScenarioValidator()
        self.references: dict = {}

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
                self.scenario.locomotives = [LocomotiveInputDTO(**data) for data in locomotive_list]

        except json.JSONDecodeError as e:
            raise BuilderError(f'Invalid JSON format in {locomotives_path}: {e!s}') from e
        except Exception as e:
            raise BuilderError(f'Failed to load locomotives from {locomotives_path}: {e!s}') from e

    def __load_routes(self, scenario_dto: ScenarioInputDTO) -> None:
        """Load routes from CSV file and map to domain models.

        Parameters
        ----------
        scenario_dto : ScenarioInputDTO
            Scenario DTO containing file references.

        Raises
        ------
        BuilderError
            If routes file is not specified or loading fails.
        """
        routes_file: str | None = scenario_dto.routes_file or self.references.get('routes')

        if not routes_file:
            raise BuilderError('Missing routes_file in scenario configuration')

        scenario_dir: Path = Path(self.scenario_path).parent
        routes_path: Path = scenario_dir / routes_file

        if not routes_path.exists():
            raise BuilderError(f'Routes file not found: {routes_path}')

        try:
            if isinstance(self.scenario, Scenario):
                with routes_path.open('r') as f:
                    routes_data = json.load(f)
                
                routes_list: list[dict[str, Any]] = routes_data.get('routes', [])
                # Map JSON fields to DTO fields
                mapped_routes = []
                for route_data in routes_list:
                    mapped_route = {
                        'route_id': route_data.get('id', ''),
                        'description': route_data.get('description'),
                        'duration': route_data.get('duration', 0.0),
                        'track_sequence': route_data.get('path', [])
                    }
                    mapped_routes.append(RouteInputDTO(**mapped_route))
                self.scenario.routes = mapped_routes

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

    def __load_scenario(self) -> ScenarioInputDTO:
        """Load scenario DTO from a JSON file.

        Returns
        -------
        ScenarioInputDTO
            Raw scenario input data.
        """
        logger.info('Loading scenario models from %s', self.scenario_path)

        try:
            with open(self.scenario_path, encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields exist before creating DTO
            required_fields = ['scenario_id', 'start_date', 'end_date']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise BuilderError(
                    f'Missing required fields {", ".join(missing_fields)} in {self.scenario_path}: '
                    f'Found fields: {", ".join(data.keys())}'
                )

            scenario_dto = ScenarioInputDTO(**data)
            # Populate references for backward compatibility
            self.references = data.get('references', {})
            logger.info('Successfully loaded scenario DTO: %s', data.get('scenario_id'))
            return scenario_dto

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

    def __load_tracks(self, scenario_dto: ScenarioInputDTO) -> None:
        """Load tracks from JSON file and map to domain models.

        Parameters
        ----------
        scenario_dto : ScenarioInputDTO
            Scenario DTO containing file references.

        Raises
        ------
        BuilderError
            If tracks file is not specified or loading fails.
        """
        tracks_file: str | None = scenario_dto.workshop_tracks_file or self.references.get('tracks')

        if not tracks_file:
            raise BuilderError('Missing workshop_tracks_file in scenario configuration')

        scenario_dir: Path = Path(self.scenario_path).parent
        tracks_path: Path = scenario_dir / tracks_file

        if not tracks_path.exists():
            raise BuilderError(f'Tracks file not found: {tracks_path}')

        try:
            if isinstance(self.scenario, Scenario):
                with tracks_path.open('r', encoding='utf-8') as f:
                    tracks_data = json.load(f)
                
                tracks_list: list[dict[str, Any]] = tracks_data.get('tracks', [])
                track_dtos = [TrackInputDTO(**track_data) for track_data in tracks_list]
                self.scenario.tracks = track_dtos

        except Exception as e:
            raise BuilderError(f'Failed to load tracks from {tracks_path}: {e!s}') from e

    def __load_trains(self, scenario_dto: ScenarioInputDTO) -> None:
        """Load trains from CSV file and map to domain models.

        Parameters
        ----------
        scenario_dto : ScenarioInputDTO
            Scenario DTO containing file references.

        Raises
        ------
        BuilderError
            If trains file is not specified or loading fails.
        """
        trains_file: str | None = scenario_dto.train_schedule_file or self.references.get('trains')

        if not trains_file:
            raise BuilderError('Missing train_schedule_file in scenario configuration')

        scenario_dir: Path = Path(self.scenario_path).parent
        trains_path: Path = scenario_dir / trains_file

        if not trains_path.exists():
            raise BuilderError(f'Trains file not found: {trains_path}')

        try:
            if isinstance(self.scenario, Scenario):
                import pandas as pd
                from configuration.application.dtos.train_input_dto import TrainInputDTO
                from configuration.application.dtos.wagon_input_dto import WagonInputDTO
                
                df = pd.read_csv(trains_path, sep=';', parse_dates=['arrival_time'])
                df['train_id'] = df['train_id'].fillna('NO_ID').astype(str)
                df['arrival_time'] = pd.to_datetime(df['arrival_time'], errors='coerce')
                
                train_dtos = []
                for train_id, group in df.groupby('train_id'):
                    latest_arrival = group['arrival_time'].max()
                    first_row = group.iloc[0]
                    
                    wagon_dtos: list[WagonInputDTO] = []
                    for _, row in group.iterrows():
                        wagon_dto = WagonInputDTO(
                            wagon_id=str(row.get('wagon_id', f'{train_id}_wagon_{len(wagon_dtos) + 1}')),
                            length=float(row.get('length', 10.0)),
                            is_loaded=bool(row.get('is_loaded', False)),
                            needs_retrofit=bool(row.get('needs_retrofit', True)),
                            track=str(row.get('Track', '')) if pd.notna(row.get('Track')) else None,
                        )
                        wagon_dtos.append(wagon_dto)
                    
                    train_dto = TrainInputDTO(
                        train_id=str(train_id),
                        arrival_time=latest_arrival.isoformat(),
                        departure_time=latest_arrival.isoformat(),
                        locomotive_id=str(first_row.get('locomotive_id', 'default_loco')),
                        route_id=str(first_row.get('route_id', 'default_route')),
                        wagons=wagon_dtos,
                    )
                    train_dtos.append(train_dto)
                
                self.scenario.trains = train_dtos

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
                # Map only required fields for DTO
                mapped_workshops = []
                for workshop_data in workshops_list:
                    mapped_workshop = {
                        'workshop_id': workshop_data.get('workshop_id', ''),
                        'track_id': workshop_data.get('track_id', ''),
                        'retrofit_stations': workshop_data.get('retrofit_stations', 0)
                    }
                    mapped_workshops.append(WorkshopInputDTO(**mapped_workshop))
                self.scenario.workshops = mapped_workshops

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
        scenario_dto = self.__load_scenario()

        # Validate DTO
        scenario_dto.model_validate(scenario_dto.model_dump())

        # Create domain model from DTO with defaults
        from configuration.domain.models.scenario import TrackSelectionStrategy, LocoDeliveryStrategy
        
        self.scenario = Scenario(
            scenario_id=scenario_dto.scenario_id,
            start_date=scenario_dto.start_date,
            end_date=scenario_dto.end_date,
            track_selection_strategy=scenario_dto.track_selection_strategy or TrackSelectionStrategy.LEAST_OCCUPIED,
            retrofit_selection_strategy=scenario_dto.retrofit_selection_strategy or TrackSelectionStrategy.LEAST_OCCUPIED,
            loco_delivery_strategy=scenario_dto.loco_delivery_strategy or LocoDeliveryStrategy.RETURN_TO_PARKING,
        )

        if isinstance(self.scenario, Scenario):
            self.__load_locomotives()
            self.__load_tracks(scenario_dto)
            self.__load_trains(scenario_dto)
            self.__load_routes(scenario_dto)
            self.__load_topology()
            self.__load_process_times()
            self.__load_workshops()
            # Validate scenario after all referenced files are loaded
            self.scenario.validate_simulation_requirements()

            # Run comprehensive validation
            validation_result = self.validator.validate(self.scenario)
            if not validation_result.is_valid:
                validation_result.print_summary()
                if validation_result.has_errors():
                    error_messages = [str(issue) for issue in validation_result.get_errors()]
                    raise BuilderError(f'Scenario validation failed: {"\n".join(error_messages)}')
                logger.warning('Scenario has validation warnings but will proceed')
        else:
            raise BuilderError('Scenario could not be loaded properly.')
        return self.scenario
