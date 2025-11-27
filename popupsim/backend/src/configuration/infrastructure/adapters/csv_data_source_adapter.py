"""CSV data source adapter for hexagonal architecture."""

from pathlib import Path
from typing import Any

from configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from configuration.application.dtos.route_input_dto import RouteInputDTO
from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO
from configuration.application.dtos.track_input_dto import TrackInputDTO
from configuration.application.dtos.train_input_dto import TrainInputDTO
from configuration.application.dtos.wagon_input_dto import WagonInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from configuration.domain.exceptions import DataSourceError
from configuration.domain.ports.data_source_port import DataSourcePort


class CsvDataSourceAdapter(DataSourcePort):
    """CSV data source adapter for loading scenario data from CSV files.

    This adapter loads scenario data from a directory containing CSV files:
    - scenario.csv: Basic scenario metadata
    - trains.csv: Train schedule data
    - wagons.csv: Wagon data (can be separate or embedded in trains.csv)
    - workshops.csv: Workshop configuration
    - tracks.csv: Track definitions
    - routes.csv: Route definitions
    - locomotives.csv: Locomotive data
    """

    def load_scenario(self, source_identifier: str | Path) -> ScenarioInputDTO:
        """Load scenario data from CSV files in a directory.

        Parameters
        ----------
        source_identifier : str | Path
            Path to directory containing CSV files

        Returns
        -------
        ScenarioInputDTO
            Complete scenario data
        """
        csv_dir = Path(source_identifier)
        if not csv_dir.is_dir():
            raise DataSourceError(f'CSV directory not found: {csv_dir}')

        # Load scenario metadata
        scenario_data = self._load_scenario_metadata(csv_dir)

        # Load all related data (methods exist for future use)
        self._load_trains(csv_dir)
        self._load_workshops(csv_dir)
        self._load_tracks(csv_dir)
        self._load_routes(csv_dir)
        self._load_locomotives(csv_dir)

        return ScenarioInputDTO(
            scenario_id=scenario_data['scenario_id'],
            start_date=scenario_data['start_date'],
            end_date=scenario_data['end_date'],
            random_seed=scenario_data.get('random_seed'),
            train_schedule_file='trains.csv',
            routes_file='routes.csv',
            workshop_tracks_file='workshops.csv',
        )

    def validate_source(self, source_identifier: str | Path) -> bool:
        """Validate CSV directory structure.

        Parameters
        ----------
        source_identifier : str | Path
            Path to CSV directory

        Returns
        -------
        bool
            True if directory contains required CSV files
        """
        csv_dir = Path(source_identifier)
        if not csv_dir.is_dir():
            return False

        required_files = ['scenario.csv', 'trains.csv', 'workshops.csv', 'tracks.csv']
        return all((csv_dir / file).exists() for file in required_files)

    def get_source_metadata(self, source_identifier: str | Path) -> dict[str, Any]:
        """Get CSV source metadata.

        Parameters
        ----------
        source_identifier : str | Path
            Path to CSV directory

        Returns
        -------
        dict[str, Any]
            Metadata about CSV files
        """
        csv_dir = Path(source_identifier)
        metadata = {
            'source_type': 'csv',
            'directory': str(csv_dir),
            'files': [],
        }

        if csv_dir.is_dir():
            csv_files = list(csv_dir.glob('*.csv'))
            metadata['files'] = [{'name': f.name} for f in csv_files]

        return metadata

    def _load_scenario_metadata(self, csv_dir: Path) -> dict[str, Any]:
        """Load scenario metadata from scenario.csv."""
        scenario_file = csv_dir / 'scenario.csv'
        if not scenario_file.exists():
            raise DataSourceError(f'scenario.csv not found in {csv_dir}')

        # Import pandas only when needed for CSV processing
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(scenario_file)
        if df.empty:
            raise DataSourceError('scenario.csv is empty')

        # Assume first row contains scenario data
        row = df.iloc[0]
        return {
            'scenario_id': row['scenario_id'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'random_seed': row.get('random_seed'),
        }

    def _load_trains(self, csv_dir: Path) -> list[TrainInputDTO]:
        """Load train data from trains.csv."""
        trains_file = csv_dir / 'trains.csv'
        if not trains_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(trains_file)
        trains = []

        for _, row in df.iterrows():
            # Load wagons for this train (could be in separate file or embedded)
            wagons = self._load_wagons_for_train(csv_dir, row['train_id'])

            trains.append(
                TrainInputDTO(
                    train_id=row['train_id'],
                    arrival_time=row['arrival_time'],
                    departure_time=row.get('departure_time', row['arrival_time']),
                    locomotive_id=row.get('locomotive_id', 'L001'),
                    route_id=row.get('route_id', 'R001'),
                    wagons=wagons,
                )
            )

        return trains

    def _load_wagons_for_train(self, csv_dir: Path, train_id: str) -> list[WagonInputDTO]:
        """Load wagon data for a specific train."""
        wagons_file = csv_dir / 'wagons.csv'
        if not wagons_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(wagons_file)
        # Filter wagons for this train
        train_wagons = df[df['train_id'] == train_id] if 'train_id' in df.columns else df

        wagons = []
        for _, row in train_wagons.iterrows():
            wagons.append(
                WagonInputDTO(
                    wagon_id=row['wagon_id'],
                    length=float(row['length']),
                    is_loaded=bool(row.get('is_loaded', False)),
                    needs_retrofit=bool(row.get('needs_retrofit', True)),
                )
            )

        return wagons

    def _load_workshops(self, csv_dir: Path) -> list[WorkshopInputDTO]:
        """Load workshop data from workshops.csv."""
        workshops_file = csv_dir / 'workshops.csv'
        if not workshops_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(workshops_file)
        workshops = []

        for _, row in df.iterrows():
            workshops.append(
                WorkshopInputDTO(
                    workshop_id=row['workshop_id'],
                    track_id=row['track_id'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    retrofit_stations=int(row.get('retrofit_stations', 1)),
                    worker=int(row.get('worker', 1)),
                )
            )

        return workshops

    def _load_tracks(self, csv_dir: Path) -> list[TrackInputDTO]:
        """Load track data from tracks.csv."""
        tracks_file = csv_dir / 'tracks.csv'
        if not tracks_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(tracks_file)
        tracks = []

        for _, row in df.iterrows():
            tracks.append(
                TrackInputDTO(
                    id=row['id'],
                    name=row['name'],
                    type=row['type'],
                    capacity=float(row.get('capacity', 1000.0)),
                    edges=row.get('edges', '').split(',') if row.get('edges') else [],
                )
            )

        return tracks

    def _load_routes(self, csv_dir: Path) -> list[RouteInputDTO]:
        """Load route data from routes.csv."""
        routes_file = csv_dir / 'routes.csv'
        if not routes_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(routes_file)
        routes = []

        for _, row in df.iterrows():
            path_list = row.get('path', '').split(',') if row.get('path') else []
            if not path_list:
                path_list = [row['from_track'], row['to_track']]
            routes.append(
                RouteInputDTO(
                    route_id=row['route_id'],
                    duration=float(row['duration']),
                    track_sequence=path_list,
                )
            )

        return routes

    def _load_locomotives(self, csv_dir: Path) -> list[LocomotiveInputDTO]:
        """Load locomotive data from locomotives.csv."""
        locomotives_file = csv_dir / 'locomotives.csv'
        if not locomotives_file.exists():
            return []

        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise DataSourceError('pandas required for CSV processing') from e

        df = pd.read_csv(locomotives_file)
        locomotives = []

        for _, row in df.iterrows():
            locomotives.append(
                LocomotiveInputDTO(
                    locomotive_id=row['locomotive_id'],
                    name=row['name'],
                    track_id=row['track_id'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                )
            )

        return locomotives
