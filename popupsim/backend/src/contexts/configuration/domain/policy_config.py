"""Policy configuration models following ADR-012."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResourceSelectionStrategy(str, Enum):
    """Resource selection strategies."""

    CLOSEST_AVAILABLE = "closest_available"
    MOST_EFFICIENT = "most_efficient"
    LOAD_BALANCED = "load_balanced"
    FIRST_AVAILABLE = "first_available"


class TrackSelectionStrategy(str, Enum):
    """Track selection strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_OCCUPIED = "least_occupied"
    SEQUENTIAL_FILL = "sequential_fill"
    BALANCED_FILL = "balanced_fill"
    SHORTEST_QUEUE = "shortest_queue"
    RANDOM = "random"


class BatchTimeoutStrategy(str, Enum):
    """Batch timeout handling strategies."""

    PARTIAL_BATCH = "partial_batch"
    WAIT_FULL = "wait_full"
    DYNAMIC = "dynamic"


class PriorityAging(str, Enum):
    """Priority aging strategies."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    NONE = "none"


class ResourceSelectionPolicy(BaseModel):
    """Policies for resource assignment."""

    locomotive_strategy: ResourceSelectionStrategy = (
        ResourceSelectionStrategy.CLOSEST_AVAILABLE
    )
    fallback_strategy: ResourceSelectionStrategy = (
        ResourceSelectionStrategy.FIRST_AVAILABLE
    )
    distance_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    efficiency_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    load_balance_weight: float = Field(default=0.3, ge=0.0, le=1.0)


class TrackSelectionPolicy(BaseModel):
    """Policies for track selection."""

    collection_strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED
    parking_strategy: TrackSelectionStrategy = TrackSelectionStrategy.SEQUENTIAL_FILL
    workshop_strategy: TrackSelectionStrategy = TrackSelectionStrategy.SHORTEST_QUEUE
    capacity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class OptimizationPolicy(BaseModel):
    """Policies for system optimization."""

    minimize_travel_distance: bool = True
    enable_load_balancing: bool = True
    energy_efficiency_mode: bool = False
    batch_optimization: bool = True
    predictive_scheduling: bool = False


class BatchProcessingConfig(BaseModel):
    """Batch processing configuration."""

    min_batch_size: int = Field(default=1, ge=1)
    max_batch_size: int = Field(default=8, ge=1)
    timeout_minutes: float = Field(default=5.0, gt=0.0)
    timeout_strategy: BatchTimeoutStrategy = BatchTimeoutStrategy.PARTIAL_BATCH


class PriorityHandlingConfig(BaseModel):
    """Priority handling configuration."""

    enable_preemption: bool = True
    priority_aging: PriorityAging = PriorityAging.LINEAR
    aging_factor: float = Field(default=1.2, gt=1.0)


class ResourceManagementConfig(BaseModel):
    """Resource management configuration."""

    allocation_timeout: float = Field(default=30.0, gt=0.0)
    retry_attempts: int = Field(default=3, ge=0)
    fallback_enabled: bool = True


class OperationalPolicy(BaseModel):
    """Policies for operational behavior."""

    batch_processing: BatchProcessingConfig = BatchProcessingConfig()
    priority_handling: PriorityHandlingConfig = PriorityHandlingConfig()
    resource_management: ResourceManagementConfig = ResourceManagementConfig()


class WorkflowPolicy(BaseModel):
    """Policies for workflow execution."""

    parallel_execution: bool = True
    conditional_branching: bool = True
    resource_optimization: bool = True
    step_timeout_minutes: float = Field(default=60.0, gt=0.0)


class PolicyConfiguration(BaseModel):
    """Central policy configuration for all contexts."""

    resource_selection: ResourceSelectionPolicy = ResourceSelectionPolicy()
    track_selection: TrackSelectionPolicy = TrackSelectionPolicy()
    optimization: OptimizationPolicy = OptimizationPolicy()
    operational: OperationalPolicy = OperationalPolicy()
    workflow: WorkflowPolicy = WorkflowPolicy()

    def model_post_init(self, __context: Any) -> None:
        """Validate policy configuration after initialization."""
        # Validate weight sums
        total_weight = (
            self.resource_selection.distance_weight
            + self.resource_selection.efficiency_weight
            + self.resource_selection.load_balance_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            msg = "Resource selection weights must sum to 1.0"
            raise ValueError(msg)

        # Validate batch size constraints
        if (
            self.operational.batch_processing.min_batch_size
            > self.operational.batch_processing.max_batch_size
        ):
            msg = "min_batch_size cannot be greater than max_batch_size"
            raise ValueError(msg)
