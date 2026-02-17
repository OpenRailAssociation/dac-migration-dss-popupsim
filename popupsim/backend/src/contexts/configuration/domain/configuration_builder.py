"""Configuration builder for loading scenarios from files."""

from pathlib import Path

from contexts.configuration.domain.models.scenario import Scenario
from contexts.configuration.infrastructure.file_loader import FileLoader


class ConfigurationBuilder:  # pylint: disable=too-few-public-methods
    """Loads scenario configuration from files."""

    def __init__(self, path: Path | str) -> None:
        """Initialize with scenario path."""
        self._path = Path(path) if isinstance(path, str) else path

    def build(self) -> Scenario:
        """Load and build scenario from file path."""
        return FileLoader(self._path).load()
