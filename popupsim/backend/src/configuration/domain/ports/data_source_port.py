"""Port interface for data source adapters."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any

from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO


class DataSourcePort(ABC):
    """Port interface for loading scenario data from various sources.

    This port defines the contract for data source adapters in hexagonal architecture.
    Adapters can implement CSV, API, database, or other data source integrations.
    """

    @abstractmethod
    def load_scenario(self, source_identifier: str | Path) -> ScenarioInputDTO:
        """Load complete scenario data from the data source.

        Parameters
        ----------
        source_identifier : str | Path
            Source-specific identifier (file path, API endpoint, etc.)

        Returns
        -------
        ScenarioInputDTO
            Complete scenario data ready for domain model creation

        Raises
        ------
        DataSourceError
            When data cannot be loaded or is invalid
        """
        raise NotImplementedError

    @abstractmethod
    def validate_source(self, source_identifier: str | Path) -> bool:
        """Validate that the data source is accessible and valid.

        Parameters
        ----------
        source_identifier : str | Path
            Source-specific identifier to validate

        Returns
        -------
        bool
            True if source is valid and accessible
        """
        raise NotImplementedError

    @abstractmethod
    def get_source_metadata(self, source_identifier: str | Path) -> dict[str, Any]:
        """Get metadata about the data source.

        Parameters
        ----------
        source_identifier : str | Path
            Source-specific identifier

        Returns
        -------
        dict[str, Any]
            Metadata including source type, version, last modified, etc.
        """
        raise NotImplementedError
