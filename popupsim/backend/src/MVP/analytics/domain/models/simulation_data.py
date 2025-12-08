"""Simulation data parameter objects for analytics."""

from dataclasses import dataclass
from typing import Any

from MVP.configuration.domain.models.scenario import Scenario
from MVP.workshop_operations.domain.entities.wagon import Wagon
from MVP.workshop_operations.domain.entities.workshop import (
    Workshop,
)


@dataclass
class SimulationData:
    """Groups simulation data for KPI calculation."""

    metrics: dict[str, list[dict[str, Any]]]
    scenario: Scenario
    wagons: list[Wagon]
    rejected_wagons: list[Wagon]
    workshops: list[Workshop]


@dataclass
class ContextData:
    """Groups context references for metrics collection."""

    popup_context: Any = None
    yard_context: Any = None
    shunting_context: Any = None
