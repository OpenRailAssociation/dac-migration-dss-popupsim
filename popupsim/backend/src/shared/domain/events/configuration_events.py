"""Configuration domain events."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigurationLoadedEvent:
    """Configuration has been loaded and validated."""

    scenario: Any
