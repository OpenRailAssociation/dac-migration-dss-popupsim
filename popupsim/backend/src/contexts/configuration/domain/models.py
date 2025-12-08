"""Configuration domain models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ConfigurationStatus(str, Enum):
    """Configuration status."""

    DRAFT = "draft"
    READY = "ready"
    INVALID = "invalid"


class ComponentStatus(str, Enum):
    """Component status."""

    MISSING = "missing"
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


@dataclass
class WorkshopConfig:
    """Workshop configuration."""

    id: str
    track: str
    retrofit_stations: int
    location: str
    capacity: int


@dataclass
class TrackConfig:
    """Track configuration."""

    id: str
    type: str
    capacity: int
    length: float
    location: str


@dataclass
class LocomotiveConfig:
    """Locomotive configuration."""

    id: str
    name: str
    max_wagons: int
    speed: float
    initial_track: str
    coupler_type: str


@dataclass
class ProcessTimesConfig:
    """Process times configuration."""

    wagon_retrofit_time: str
    locomotive_movement_time: str
    coupling_time: str
    decoupling_time: str


@dataclass
class TopologyConnection:
    """Topology connection."""

    from_track: str
    to_track: str
    distance: float
    travel_time: float


@dataclass
class TopologyConfig:
    """Topology configuration."""

    connections: list[TopologyConnection]


@dataclass
class StrategiesConfig:
    """Selection strategies configuration."""

    track_selection_strategy: str
    retrofit_selection_strategy: str
    loco_delivery_strategy: str


@dataclass
class ScenarioMetadata:
    """Scenario metadata."""

    id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime


@dataclass
class ComponentInfo:
    """Component information."""

    name: str
    status: ComponentStatus
    count: int
    validation_issues: list[str]


@dataclass
class ConfigurationState:
    """Complete configuration state."""

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
