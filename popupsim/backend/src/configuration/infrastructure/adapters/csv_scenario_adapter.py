"""CSV scenario adapter (Hexagonal Architecture)."""

from pathlib import Path
from typing import Any

from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO
from configuration.application.dtos.train_input_dto import TrainInputDTO
from configuration.application.dtos.wagon_input_dto import WagonInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from configuration.domain.ports.scenario_port import ScenarioPort


class CsvScenarioAdapter(ScenarioPort):
    """Adapter for loading scenarios from CSV directories."""

    def supports(self, source: Path) -> bool:
        """Check if source is a CSV directory."""
        return source.is_dir() and (source / 'scenario.csv').exists()

    def load_scenario_dto(self, source: Path) -> ScenarioInputDTO:
        """Load scenario DTO from CSV directory."""
        return self._load_csv_data(source)

    def _load_csv_data(self, source: Path) -> ScenarioInputDTO:
        """Load CSV data into DTO."""
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise ImportError('pandas required for CSV processing') from e

        # Load CSV files
        scenario_df = pd.read_csv(source / 'scenario.csv')
        trains_df = pd.read_csv(source / 'trains.csv')
        wagons_df = pd.read_csv(source / 'wagons.csv')
        workshops_df = pd.read_csv(source / 'workshops.csv')
        tracks_df = pd.read_csv(source / 'tracks.csv')

        scenario_data = scenario_df.to_dict('records')[0]

        # Process trains with wagons
        trains_data = self._process_trains(trains_df, wagons_df)
        workshops_data = self._process_workshops(workshops_df)

        # Use tracks_df for validation
        if tracks_df.empty:
            raise ValueError('tracks.csv cannot be empty')

        return ScenarioInputDTO(
            id=scenario_data['id'],
            start_date=scenario_data['start_date'],
            end_date=scenario_data['end_date'],
            track_selection_strategy=scenario_data.get('track_selection_strategy'),
            retrofit_selection_strategy=scenario_data.get('retrofit_selection_strategy'),
            loco_delivery_strategy=scenario_data.get('loco_delivery_strategy'),
            trains=trains_data,
            workshops=workshops_data,
        )

    def _process_trains(self, trains_df: Any, wagons_df: Any) -> list[TrainInputDTO]:
        """Process trains and wagons DataFrames into DTOs."""
        trains = []
        for _, train_row in trains_df.iterrows():
            # Get wagons for this train
            train_wagons = wagons_df[wagons_df['id'] == train_row['id']]
            wagon_dtos = [
                WagonInputDTO(
                    id=str(wagon_row['id']),
                    length=float(wagon_row['length']),
                    is_loaded=bool(wagon_row.get('is_loaded', False)),
                    needs_retrofit=bool(wagon_row.get('needs_retrofit', True)),
                    track=wagon_row.get('track'),
                )
                for _, wagon_row in train_wagons.iterrows()
            ]

            trains.append(
                TrainInputDTO(
                    id=str(train_row['id']),
                    arrival_time=str(train_row['arrival_time']),
                    departure_time=str(train_row['departure_time']),
                    locomotive_id=str(train_row.get('locomotive_id', '')),
                    route_id=str(train_row.get('route_id', '')),
                    wagons=wagon_dtos,
                    priority=train_row.get('priority'),
                )
            )
        return trains

    def _process_workshops(self, workshops_df: Any) -> list[WorkshopInputDTO]:
        """Process workshops DataFrame into DTOs."""
        return [
            WorkshopInputDTO(
                id=str(row['id']),
                track_id=str(row['track_id']),
                retrofit_stations=int(row['retrofit_stations']),
            )
            for _, row in workshops_df.iterrows()
        ]
