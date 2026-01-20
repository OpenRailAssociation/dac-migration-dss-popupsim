"""Rake formation request objects for parameter reduction."""

from dataclasses import dataclass

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


@dataclass
class RakeFormationRequest:
    """Request object for rake formation operations.

    Encapsulates all parameters needed for rake formation to reduce
    method parameter counts and improve maintainability.
    """

    rake_id: str
    wagons: list[Wagon]
    rake_type: RakeType
    formation_track: str
    target_track: str
    formation_time: float
