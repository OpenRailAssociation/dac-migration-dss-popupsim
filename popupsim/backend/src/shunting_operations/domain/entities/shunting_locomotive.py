"""Shunting locomotive entity - specialized for shunting operations."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.wagon import CouplerType

from .shunting_operation import ShuntingOperation


class ShuntingStatus(Enum):
    """Shunting-specific locomotive status."""

    IDLE = 'idle'
    MOVING = 'moving'
    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'
    POSITIONING = 'positioning'


@dataclass
class CapacityLimits:
    """Capacity constraints for shunting locomotive."""

    max_wagon_capacity: int
    max_weight_tons: float
    max_consist_length_m: float


@dataclass
class CurrentLoad:
    """Current load state of shunting locomotive."""

    coupled_wagons: int = 0
    current_weight_tons: float = 0.0
    current_consist_length_m: float = 0.0


@dataclass
class MovementState:
    """Movement and operational state."""

    current_track: str
    shunting_status: ShuntingStatus = ShuntingStatus.IDLE
    target_track: str | None = None


@dataclass
class ShuntingLocomotive:
    """Locomotive specialized for shunting operations."""

    base_locomotive: Locomotive
    capacity_limits: CapacityLimits
    supported_coupler_types: list[CouplerType]
    movement_state: MovementState
    current_load: CurrentLoad = field(default_factory=CurrentLoad)
    operation_queue: list[ShuntingOperation] = field(default_factory=list)

    @property
    def id(self) -> str:
        """Get locomotive ID.

        Returns
        -------
        str
            Id of the locomotive
        """
        return self.base_locomotive.id

    def start_movement(self, target: str) -> None:
        """Start movement to target track.

        Parameters
        ----------
        target : str
            Target track identifier
        """
        self.movement_state.target_track = target
        self.movement_state.shunting_status = ShuntingStatus.MOVING

    def complete_movement(self) -> None:
        """Complete movement operation."""
        if self.movement_state.target_track:
            self.movement_state.current_track = self.movement_state.target_track
            self.movement_state.target_track = None
        self.movement_state.shunting_status = ShuntingStatus.IDLE

    def can_couple_wagon(self, wagon_coupler_type: CouplerType) -> bool:
        """Check if locomotive can couple to wagon with given coupler type.

        Parameters
        ----------
        wagon_coupler_type : CouplerType
            The coupler type of the wagon to couple

        Returns
        -------
        bool
            True if coupling is possible, False otherwise
        """
        # HYBRID can couple to both SCREW and DAC
        if CouplerType.HYBRID in self.supported_coupler_types:
            return True

        # Direct match required for non-hybrid couplers
        return wagon_coupler_type in self.supported_coupler_types

    def add_operation(self, operation: ShuntingOperation) -> None:
        """Add operation to the queue.

        Parameters
        ----------
        operation : ShuntingOperation
            Operation to add to the queue
        """
        self.operation_queue.append(operation)

    def get_next_operation(self) -> ShuntingOperation | None:
        """Get next operation from queue.

        Returns
        -------
        Optional[ShuntingOperation]
            Next operation or None if queue is empty
        """
        return self.operation_queue.pop(0) if self.operation_queue else None

    def is_at_capacity(self) -> bool:
        """Check if locomotive is at maximum capacity.

        Returns
        -------
        bool
            True if at any capacity limit, False otherwise
        """
        return (
            self.current_load.coupled_wagons >= self.capacity_limits.max_wagon_capacity
            or self.current_load.current_weight_tons >= self.capacity_limits.max_weight_tons
            or self.current_load.current_consist_length_m >= self.capacity_limits.max_consist_length_m
        )

    def get_capacity_utilization(self) -> dict[str, float]:
        """Get current capacity utilization as percentages.

        Returns
        -------
        dict[str, float]
            Utilization percentages for wagon count, weight, and length
        """
        return {
            'wagon_utilization': (self.current_load.coupled_wagons / self.capacity_limits.max_wagon_capacity) * 100,
            'weight_utilization': (self.current_load.current_weight_tons / self.capacity_limits.max_weight_tons) * 100,
            'length_utilization': (
                self.current_load.current_consist_length_m / self.capacity_limits.max_consist_length_m
            )
            * 100,
        }
