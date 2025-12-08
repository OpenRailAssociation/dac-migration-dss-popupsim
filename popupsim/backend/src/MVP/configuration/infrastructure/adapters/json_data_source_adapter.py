"""JSON data source adapter (existing functionality wrapped in hexagonal architecture)."""

import json
from pathlib import Path
from typing import Any

from MVP.configuration.application.dtos.scenario_input_dto import (
    ScenarioInputDTO,
)
from MVP.configuration.domain.exceptions import DataSourceError
from MVP.configuration.domain.ports.data_source_port import (
    DataSourcePort,
)


class JsonDataSourceAdapter(DataSourcePort):
    """JSON data source adapter wrapping existing JSON loading functionality.

    This adapter maintains compatibility with existing JSON-based scenarios
    while conforming to the hexagonal architecture pattern.
    """

    def load_scenario(self, source_identifier: str | Path) -> ScenarioInputDTO:
        """Load scenario data from JSON file.

        Parameters
        ----------
        source_identifier : str | Path
            Path to scenario JSON file

        Returns
        -------
        ScenarioInputDTO
            Complete scenario data
        """
        json_file = Path(source_identifier)
        if not json_file.exists():
            msg = f"JSON file not found: {json_file}"
            raise DataSourceError(msg)

        try:
            with json_file.open("r", encoding="utf-8") as f:
                json.load(f)  # Validate JSON format
        except (json.JSONDecodeError, OSError) as e:
            msg = f"Failed to load JSON file: {e}"
            raise DataSourceError(msg) from e

        # Use existing ScenarioBuilder logic for JSON loading
        # pylint: disable=import-outside-toplevel
        from configuration.application.scenario_builder import ScenarioBuilder

        builder = ScenarioBuilder(json_file)
        scenario = builder.build()

        # Convert domain model back to DTO for consistency
        return self._convert_scenario_to_dto(scenario)

    def validate_source(self, source_identifier: str | Path) -> bool:
        """Validate JSON file exists and is valid JSON.

        Parameters
        ----------
        source_identifier : str | Path
            Path to JSON file

        Returns
        -------
        bool
            True if file exists and contains valid JSON
        """
        json_file = Path(source_identifier)
        if not json_file.exists():
            return False

        try:
            with json_file.open("r", encoding="utf-8") as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def get_source_metadata(self, source_identifier: str | Path) -> dict[str, Any]:
        """Get JSON file metadata.

        Parameters
        ----------
        source_identifier : str | Path
            Path to JSON file

        Returns
        -------
        dict[str, Any]
            Metadata about JSON file
        """
        json_file = Path(source_identifier)
        metadata: dict[str, Any] = {
            "source_type": "json",
            "file_path": str(json_file),
        }

        if json_file.exists():
            stat = json_file.stat()
            metadata.update(
                {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "exists": True,
                }
            )
        else:
            metadata["exists"] = False

        return metadata

    def _convert_scenario_to_dto(self, scenario: Any) -> ScenarioInputDTO:
        """Convert domain scenario back to DTO format.

        This is a temporary bridge method until full hexagonal architecture
        is implemented throughout the system.
        """
        # For now, create a minimal DTO with basic scenario data
        # This will be expanded as the hexagonal architecture is completed
        start_date = (
            scenario.start_date.isoformat()
            if hasattr(scenario.start_date, "isoformat")
            else str(scenario.start_date)
        )
        end_date = (
            scenario.end_date.isoformat()
            if hasattr(scenario.end_date, "isoformat")
            else str(scenario.end_date)
        )
        return ScenarioInputDTO(
            id=scenario.id,
            start_date=start_date,
            end_date=end_date,
            random_seed=getattr(scenario, "random_seed", None),
        )
