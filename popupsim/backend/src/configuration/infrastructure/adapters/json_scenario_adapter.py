"""JSON scenario adapter (Hexagonal Architecture)."""

import json
from pathlib import Path

from configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from configuration.application.dtos.route_input_dto import RouteInputDTO
from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO
from configuration.application.dtos.track_input_dto import TrackInputDTO
from configuration.application.dtos.train_input_dto import TrainInputDTO
from configuration.application.dtos.wagon_input_dto import WagonInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from configuration.domain.ports.scenario_port import ScenarioPort


class JsonScenarioAdapter(ScenarioPort):
    """Adapter for loading scenario DTOs from JSON files.

    Implements the ScenarioPort interface to load scenario configuration
    from JSON files with support for external file references. Handles
    nested data structures and converts them to appropriate DTO objects.
    """

    def supports(self, source: Path) -> bool:
        """Check if source is a JSON file.

        Parameters
        ----------
        source : Path
            Path to check for JSON file compatibility.

        Returns
        -------
        bool
            True if source is an existing JSON file, False otherwise.
        """
        return source.is_file() and source.suffix == '.json'

    def load_scenario_dto(self, source: Path) -> ScenarioInputDTO:
        """Load scenario DTO from JSON file.

        Parameters
        ----------
        source : Path
            Path to JSON file containing scenario configuration.

        Returns
        -------
        ScenarioInputDTO
            Scenario data transfer object with all nested data loaded.

        Raises
        ------
        FileNotFoundError
            If the JSON file does not exist.
        json.JSONDecodeError
            If the JSON file contains invalid JSON syntax.
        """
        return self._load_scenario_dto(source)

    def _load_scenario_dto(self, source: Path) -> ScenarioInputDTO:
        """Load scenario DTO from JSON file with reference resolution.

        Parameters
        ----------
        source : Path
            Path to JSON file to load.

        Returns
        -------
        ScenarioInputDTO
            Processed scenario DTO with all references resolved.
        """
        with source.open('r', encoding='utf-8') as f:
            data = json.load(f)

        # Load referenced files if they exist
        if 'references' in data:
            self._load_references(data, source.parent)

        return self._process_json_data(data)

    def _process_json_data(self, data: dict) -> ScenarioInputDTO:
        """Process JSON data into DTO with nested objects.

        Parameters
        ----------
        data : dict
            Raw JSON data dictionary.

        Returns
        -------
        ScenarioInputDTO
            Structured DTO with all nested objects properly constructed.
        """
        # Process trains with wagons
        trains = None
        if 'trains' in data:
            trains = [
                TrainInputDTO(
                    id=train['id'],
                    arrival_time=train['arrival_time'],
                    departure_time=train['departure_time'],
                    wagons=[WagonInputDTO(**wagon) for wagon in train.get('wagons', [])],
                )
                for train in data['trains']
            ]

        # Process other collections
        workshops = [WorkshopInputDTO(**w) for w in data.get('workshops', [])]
        routes = [
            RouteInputDTO(
                id=r.get('id'), track_sequence=r.get('path', r.get('track_sequence', [])), duration=r.get('duration')
            )
            for r in data.get('routes', [])
        ]
        locomotives = [LocomotiveInputDTO(**loco) for loco in data.get('locomotives', [])]
        tracks = [TrackInputDTO(**track) for track in data.get('tracks', [])]

        return ScenarioInputDTO(
            id=data.get('id'),
            start_date=data['start_date'],
            end_date=data['end_date'],
            track_selection_strategy=data.get('track_selection_strategy'),
            retrofit_selection_strategy=data.get('retrofit_selection_strategy'),
            loco_delivery_strategy=data.get('loco_delivery_strategy'),
            trains=trains,
            workshops=workshops,
            routes=routes,
            locomotives=locomotives,
            tracks=tracks,
            topology=data.get('topology'),
        )

    def _load_references(self, data: dict, base_path: Path) -> None:
        """Load referenced JSON files and merge into data.

        Parameters
        ----------
        data : dict
            Main JSON data dictionary with 'references' section.
        base_path : Path
            Base directory path for resolving relative file references.
        """
        references = data.get('references', {})

        # Define reference types and their data keys
        reference_configs = [
            ('locomotives', 'locomotives'),
            ('routes', 'routes'),
            ('workshops', 'workshops'),
            ('tracks', 'tracks'),
            ('topology', None),  # topology uses the entire data
        ]

        for ref_key, data_key in reference_configs:
            if ref_key in references:
                filename = references[ref_key]
                ref_file = base_path / filename
                if ref_file.exists():
                    with ref_file.open('r', encoding='utf-8') as f:
                        ref_data = json.load(f)
                        if data_key is None:
                            data[ref_key] = ref_data
                        else:
                            data[ref_key] = ref_data.get(data_key, [])
