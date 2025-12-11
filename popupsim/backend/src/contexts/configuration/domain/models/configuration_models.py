"""Configuration models for step-by-step scenario building."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ComponentStatus(str, Enum):
    """Status of configuration component."""

    MISSING = 'missing'
    INCOMPLETE = 'incomplete'
    COMPLETE = 'complete'


class ConfigurationStatus(str, Enum):
    """Overall configuration status."""

    DRAFT = 'draft'
    INVALID = 'invalid'
    READY = 'ready'


@dataclass
class ScenarioMetadata:
    """Scenario metadata."""

    id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime


@dataclass
class WorkshopConfig:
    """Workshop configuration."""

    id: str
    track: str
    retrofit_stations: int


@dataclass
class TrackConfig:
    """Track configuration."""

    id: str
    # capacity: int


@dataclass
class LocomotiveConfig:
    """Locomotive configuration."""

    id: str
    max_wagons: int


@dataclass
class ProcessTimesConfig:
    """Process times configuration."""

    retrofit_time: float


@dataclass
class TopologyConfig:
    """Topology configuration."""

    connections: list['ConnectionConfig']


@dataclass
class ConnectionConfig:
    """Connection between tracks."""

    from_track: str
    to_track: str
    duration: float


@dataclass
class StrategiesConfig:
    """Selection strategies configuration."""

    track_selection: str
    retrofit_selection: str


@dataclass
class ComponentInfo:
    """Component information."""

    name: str
    status: ComponentStatus
    count: int
    validation_issues: list[str]


@dataclass
class ConfigurationState:
    """Configuration state."""

    scenario_id: str
    metadata: ScenarioMetadata
    status: ConfigurationStatus
    completion_percentage: int
    components: dict[str, ComponentInfo]
    workshops: list[WorkshopConfig]
    tracks: list[TrackConfig]
    locomotives: list[LocomotiveConfig]
    process_times: ProcessTimesConfig | None
    topology: TopologyConfig | None
    strategies: StrategiesConfig | None
    validation_issues: list[str]
    can_finalize: bool
