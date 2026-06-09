"""Input DTOs for configuration data."""

from .locomotive_input_dto import LocomotiveInputDTO
from .route_input_dto import RouteInputDTO
from .task_priority_input_dto import HoldConditionInputDTO
from .task_priority_input_dto import PriorityRuleInputDTO
from .task_priority_input_dto import TaskPriorityInputDTO
from .track_input_dto import TrackInputDTO
from .workshop_input_dto import WorkshopInputDTO

__all__ = [
    'HoldConditionInputDTO',
    'LocomotiveInputDTO',
    'PriorityRuleInputDTO',
    'RouteInputDTO',
    'TaskPriorityInputDTO',
    'TrackInputDTO',
    'WorkshopInputDTO',
]
