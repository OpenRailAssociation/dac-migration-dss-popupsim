"""Hexagonal architecture scenario loader using data source adapters."""

from pathlib import Path
from typing import Any

from MVP.configuration.application.dtos.scenario_input_dto import (
    ScenarioInputDTO,
)
from MVP.configuration.domain.exceptions import DataSourceError
from MVP.configuration.domain.ports.data_source_port import (
    DataSourcePort,
)
from MVP.configuration.infrastructure.adapters.data_source_factory import (
    DataSourceFactory,
)


class ScenarioLoader:
    """Hexagonal architecture scenario loader.

    This class uses data source adapters to load scenario data from various sources
    while maintaining separation between domain logic and infrastructure concerns.
    """

    def __init__(self, data_source_adapter: DataSourcePort | None = None) -> None:
        """Initialize scenario loader.

        Parameters
        ----------
        data_source_adapter : DataSourcePort | None
            Specific adapter to use, or None to auto-detect
        """
        self._adapter = data_source_adapter

    def load_scenario(self, source_identifier: str | Path) -> ScenarioInputDTO:
        """Load scenario data using appropriate adapter.

        Parameters
        ----------
        source_identifier : str | Path
            Source identifier (file path, directory, URL, etc.)

        Returns
        -------
        ScenarioInputDTO
            Complete scenario data ready for domain model creation

        Raises
        ------
        DataSourceError
            When data cannot be loaded or adapter fails
        """
        # Use provided adapter or auto-detect
        adapter = self._adapter or DataSourceFactory.create_adapter(source_identifier)

        # Validate source before loading
        if not adapter.validate_source(source_identifier):
            msg = f"Invalid or inaccessible data source: {source_identifier}"
            raise DataSourceError(msg)

        # Load scenario data
        return adapter.load_scenario(source_identifier)

    def get_source_info(self, source_identifier: str | Path) -> dict[str, Any]:
        """Get information about the data source.

        Parameters
        ----------
        source_identifier : str | Path
            Source identifier to inspect

        Returns
        -------
        dict[str, any]
            Source metadata and validation status
        """
        try:
            adapter = self._adapter or DataSourceFactory.create_adapter(
                source_identifier
            )
            metadata = adapter.get_source_metadata(source_identifier)
            metadata["valid"] = adapter.validate_source(source_identifier)
            return metadata
        except DataSourceError as e:
            return {
                "valid": False,
                "error": str(e),
                "source_type": "unknown",
            }

    @staticmethod
    def get_supported_sources() -> list[str]:
        """Get list of supported data source types.

        Returns
        -------
        list[str]
            List of supported source types
        """
        return DataSourceFactory.get_supported_types()
