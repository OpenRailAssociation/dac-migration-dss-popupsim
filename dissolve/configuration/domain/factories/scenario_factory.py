"""Domain factory for creating scenarios."""

from datetime import datetime
from pathlib import Path

from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO
from configuration.domain.models.scenario import (
    LocoDeliveryStrategy,
    Scenario,
    TrackSelectionStrategy,
)
from configuration.domain.models.topology import Topology
from configuration.infrastructure.adapters.json_scenario_adapter import (
    JsonScenarioAdapter,
)


class ScenarioFactory:
    """Factory for creating domain scenarios from DTOs.

    Handles the transformation of data transfer objects (DTOs) into
    domain scenario objects with proper type conversion and default
    value assignment for strategy enums.
    """

    @staticmethod
    def from_dto(dto: ScenarioInputDTO) -> Scenario:
        """Create scenario domain object from input DTO.

        Converts DTO data into domain model with proper type transformations:
        - String dates to datetime objects
        - Strategy strings to enum values with defaults
        - Preserves nested collections (trains, workshops, etc.)

        Parameters
        ----------
        dto : ScenarioInputDTO
            Input data transfer object containing scenario configuration.

        Returns
        -------
        Scenario
            Domain scenario object with validated and transformed data.

        Raises
        ------
        ValueError
            If date strings cannot be parsed or strategy values are invalid.
        """
        # Convert topology if present
        topology = None
        if dto.topology:
            topology = Topology(dto.topology)

        return Scenario(
            id=dto.id,
            start_date=datetime.fromisoformat(str(dto.start_date)),
            end_date=datetime.fromisoformat(str(dto.end_date)),
            track_selection_strategy=TrackSelectionStrategy(
                dto.track_selection_strategy or "least_occupied"
            ),
            retrofit_selection_strategy=TrackSelectionStrategy(
                dto.retrofit_selection_strategy or "least_occupied"
            ),
            loco_delivery_strategy=LocoDeliveryStrategy(
                dto.loco_delivery_strategy or "return_to_parking"
            ),
            trains=dto.trains,
            workshops=dto.workshops,
            routes=dto.routes,
            locomotives=dto.locomotives,
            tracks=dto.tracks,
            topology=topology,
        )

    @staticmethod
    def from_json_file(json_path: Path) -> Scenario:
        """Create scenario from JSON file.

        Parameters
        ----------
        json_path : Path
            Path to JSON scenario file.

        Returns
        -------
        Scenario
            Domain scenario object loaded from JSON.
        """
        adapter = JsonScenarioAdapter()
        dto = adapter.load_scenario_dto(json_path)
        return ScenarioFactory.from_dto(dto)
