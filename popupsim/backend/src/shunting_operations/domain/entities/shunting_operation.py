"""Shunting operation entity."""

from dataclasses import dataclass
from enum import Enum

from workshop_operations.domain.entities.wagon import CouplerType


class ShuntingOperationType(Enum):
    """Types of shunting operations."""

    MOVE = 'move'
    COUPLE = 'couple'
    DECOUPLE = 'decouple'
    POSITION = 'position'


@dataclass
class ShuntingOperation:
    """Represents a single shunting operation."""

    operation_type: ShuntingOperationType
    locomotive_id: str
    from_track: str
    to_track: str
    wagon_count: int = 0
    coupler_type: CouplerType | None = None
    estimated_duration: float = 0.0

    def is_movement_operation(self) -> bool:
        """Check if operation involves locomotive movement."""
        return self.operation_type in (ShuntingOperationType.MOVE, ShuntingOperationType.POSITION)

    def is_coupling_operation(self) -> bool:
        """Check if operation involves coupling/decoupling."""
        return self.operation_type in (ShuntingOperationType.COUPLE, ShuntingOperationType.DECOUPLE)
