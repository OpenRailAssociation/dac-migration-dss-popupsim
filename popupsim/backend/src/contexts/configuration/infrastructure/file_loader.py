"""File-based scenario loader."""

# ruff: noqa: C901, PLR0912, PLR0915
import json
from pathlib import Path
from typing import Any

from contexts.configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from contexts.configuration.application.dtos.route_input_dto import RouteInputDTO
from contexts.configuration.application.dtos.track_input_dto import TrackInputDTO
from contexts.configuration.application.dtos.train_input_dto import TrainInputDTO
from contexts.configuration.application.dtos.wagon_input_dto import WagonInputDTO
from contexts.configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.configuration.domain.models.scenario import LocoDeliveryStrategy
from contexts.configuration.domain.models.scenario import Scenario
from contexts.configuration.domain.models.scenario import TrackSelectionStrategy
from contexts.configuration.domain.models.topology import Topology
import pandas as pd


class FileLoader:  # pylint: disable=too-few-public-methods
    """Load scenario from file system."""

    def __init__(self, path: Path) -> None:
        self.path = path if path.is_dir() else path.parent
        self.scenario_file = path if path.is_file() else path / 'scenario.json'

    def load(self) -> Any:  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Load scenario from files."""
        with open(self.scenario_file, encoding='utf-8') as f:
            data = json.load(f)

        refs = data.get('references', {})

        scenario = Scenario(
            id=data.get('id') or data.get('scenario_id'),
            start_date=data['start_date'],
            end_date=data['end_date'],
            track_selection_strategy=data.get('track_selection_strategy') or TrackSelectionStrategy.LEAST_OCCUPIED,
            retrofit_selection_strategy=data.get('retrofit_selection_strategy')
            or TrackSelectionStrategy.LEAST_OCCUPIED,
            loco_delivery_strategy=data.get('loco_delivery_strategy') or LocoDeliveryStrategy.RETURN_TO_PARKING,
        )

        # Load locomotives (inline or from file)
        if 'locomotives' in data:
            scenario.locomotives = [LocomotiveInputDTO(**loco) for loco in data['locomotives']]
        elif 'locomotives' in refs:
            with open(self.path / refs['locomotives'], encoding='utf-8') as f:
                loco_data = json.load(f)
            scenario.locomotives = [LocomotiveInputDTO(**loco) for loco in loco_data['locomotives']]

        # Load topology first to get edge lengths (if using references)
        edge_lengths = {}
        if 'topology' in refs:
            with open(self.path / refs['topology'], encoding='utf-8') as f:
                topology_data = json.load(f)
            edge_lengths = {edge_id: edge_data['length'] for edge_id, edge_data in topology_data['edges'].items()}

        # Load workshops (inline or from file)
        if 'workshops' in data:
            scenario.workshops = [
                WorkshopInputDTO(
                    id=w.get('id') or w.get('workshop_id'),
                    track=w.get('track') or w.get('track_id'),
                    retrofit_stations=w['retrofit_stations'],
                )
                for w in data['workshops']
            ]
        elif 'workshops' in refs:
            with open(self.path / refs['workshops'], encoding='utf-8') as f:
                ws_data = json.load(f)
            scenario.workshops = [
                WorkshopInputDTO(id=w['id'], track=w['track'], retrofit_stations=w['retrofit_stations'])
                for w in ws_data['workshops']
            ]

        # Load tracks (inline or from file)
        if 'tracks' in data:
            tracks = []
            for t in data['tracks']:
                track_length = t.get(
                    'capacity', t.get('length', sum(edge_lengths.get(edge, 0.0) for edge in t.get('edges', [])))
                )
                tracks.append(
                    TrackInputDTO(
                        id=t['id'],
                        type=t.get('type', 'standard'),
                        length=track_length,
                        fillfactor=t.get('fillfactor', 0.75),
                    )
                )
            scenario.tracks = tracks
        elif 'tracks' in refs:
            with open(self.path / refs['tracks'], encoding='utf-8') as f:
                track_data = json.load(f)
            tracks = []
            for t in track_data['tracks']:
                track_length = t.get('length', sum(edge_lengths.get(edge, 0.0) for edge in t.get('edges', [])))
                tracks.append(
                    TrackInputDTO(
                        id=t['id'],
                        type=t.get('type', 'standard'),
                        length=track_length,
                        fillfactor=t.get('fillfactor', 0.75),
                    )
                )
            scenario.tracks = tracks

        # Load routes (inline or from file)
        if 'routes' in data:
            routes: list[RouteInputDTO] = []
            for r in data['routes']:
                routes.append(
                    RouteInputDTO(
                        id=r.get('id') or r.get('route_id'),
                        description=r.get('description'),
                        duration=r['duration'],
                        track_sequence=r['track_sequence'],
                    )
                )
            scenario.routes = routes
        elif 'routes' in refs:
            with open(self.path / refs['routes'], encoding='utf-8') as f:
                route_data = json.load(f)
            routes = []
            for r in route_data['routes']:
                routes.append(
                    RouteInputDTO(
                        id=r.get('id') or r.get('route_id'),
                        description=r.get('description'),
                        duration=r['duration'],
                        track_sequence=r['path'],
                    )
                )
            scenario.routes = routes

        # Load trains (inline or from file)
        if 'trains' in data:
            train_dtos = []
            for t in data['trains']:
                wagon_dtos = [
                    WagonInputDTO(
                        id=w.get('id') or w.get('wagon_id'),
                        length=w['length'],
                        is_loaded=w.get('is_loaded', False),
                        needs_retrofit=w.get('needs_retrofit', True),
                        track=w.get('track'),
                    )
                    for w in t['wagons']
                ]
                train_dtos.append(
                    TrainInputDTO(
                        train_id=t.get('train_id'),
                        arrival_time=t['arrival_time'],
                        departure_time=t['departure_time'],
                        locomotive_id=t['locomotive_id'],
                        route_id=t['route_id'],
                        wagons=wagon_dtos,
                    )
                )
            scenario.trains = train_dtos
        else:
            # Load from CSV file
            csv_file = self.path / data.get('train_schedule_file', refs.get('trains'))
            # Detect delimiter by checking first line
            with open(csv_file, encoding='utf-8') as f:
                first_line = f.readline()
                delimiter = ';' if ';' in first_line else ','

            df = pd.read_csv(csv_file, sep=delimiter, parse_dates=['arrival_time'])
            df['train_id'] = df['train_id'].fillna('NO_ID').astype(str)
            train_dtos = []
            for train_id, group in df.groupby('train_id'):
                latest_arrival = group['arrival_time'].max()
                first_row = group.iloc[0]
                wagon_dtos = [
                    WagonInputDTO(
                        id=str(row.get('wagon_id', f'{train_id}_wagon_{i + 1}')),
                        length=float(row.get('length', 10.0)),
                        is_loaded=bool(row.get('is_loaded', False)),
                        needs_retrofit=bool(row.get('needs_retrofit', True)),
                        track=str(row.get('Track')) if pd.notna(row.get('Track')) else None,
                    )
                    for i, (_, row) in enumerate(group.iterrows())
                ]
                train_dtos.append(
                    TrainInputDTO(
                        train_id=str(train_id),
                        arrival_time=latest_arrival.isoformat(),
                        departure_time=latest_arrival.isoformat(),
                        locomotive_id=str(first_row.get('locomotive_id', 'default_loco')),
                        route_id=str(first_row.get('route_id', 'default_route')),
                        wagons=wagon_dtos,
                    )
                )
            scenario.trains = train_dtos

        # Load topology and process times (if using references)
        if 'topology' in refs:
            scenario.topology = Topology(self.path / refs['topology'])
        if 'process_times' in refs:
            scenario.process_times = ProcessTimes.load_from_file(self.path / refs['process_times'])
        elif 'process_times' in data:
            scenario.process_times = ProcessTimes(**data['process_times'])

        return scenario
