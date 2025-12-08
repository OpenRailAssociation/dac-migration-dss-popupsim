"""Factory for creating appropriate data source adapters."""

from pathlib import Path

from MVP.configuration.domain.exceptions import DataSourceError
from MVP.configuration.domain.ports.data_source_port import (
    DataSourcePort,
)
from MVP.configuration.infrastructure.adapters.csv_data_source_adapter import (
    CsvDataSourceAdapter,
)
from MVP.configuration.infrastructure.adapters.json_data_source_adapter import (
    JsonDataSourceAdapter,
)


class DataSourceFactory:
    """Factory for creating data source adapters based on source type."""

    @staticmethod
    def create_adapter(source_identifier: str | Path) -> DataSourcePort:
        """Create appropriate data source adapter based on source type.

        Parameters
        ----------
        source_identifier : str | Path
            Source identifier (file path, directory, URL, etc.)

        Returns
        -------
        DataSourcePort
            Appropriate adapter for the source type

        Raises
        ------
        DataSourceError
            When source type cannot be determined or is unsupported
        """
        path = Path(source_identifier)

        # Determine adapter type based on source characteristics
        if path.is_file() and path.suffix.lower() == ".json":
            return JsonDataSourceAdapter()
        if path.is_dir():
            # Check if directory contains CSV files
            csv_files = list(path.glob("*.csv"))
            if csv_files:
                return CsvDataSourceAdapter()
            msg = f"No CSV files found in directory: {path}"
            raise DataSourceError(msg)
        if str(source_identifier).startswith(("http://", "https://")):
            # Future: API adapter
            msg = "API data source not yet implemented"
            raise DataSourceError(msg)
        msg = f"Unsupported data source type: {source_identifier}"
        raise DataSourceError(msg)

    @staticmethod
    def get_supported_types() -> list[str]:
        """Get list of supported data source types.

        Returns
        -------
        list[str]
            List of supported source types
        """
        return ["json", "csv", "api (planned)"]

    @staticmethod
    def register_adapter(source_type: str, adapter_class: type[DataSourcePort]) -> None:
        """Register a custom data source adapter.

        Parameters
        ----------
        source_type : str
            Source type identifier
        adapter_class : Type[DataSourcePort]
            Adapter class implementing DataSourcePort

        Note
        ----
        This method is reserved for future extensibility when
        custom adapters need to be registered dynamically.
        """
        # Future implementation for dynamic adapter registration
        msg = "Dynamic adapter registration not yet implemented"
        raise NotImplementedError(msg)
