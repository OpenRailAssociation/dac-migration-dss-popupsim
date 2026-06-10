"""Task priority value objects for locomotive dispatch.

This module defines the domain model for priority-based locomotive task
dispatching. Tasks are prioritized based on configurable base priorities
and dynamic rules that react to track fill levels.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum


class TaskType(StrEnum):
    """Types of locomotive tasks in the retrofit workflow.

    Each task type represents a movement operation that requires
    a locomotive to transport wagons between track types.
    """

    COLLECTION_TO_RETROFIT = 'collection_to_retrofit'
    """Move wagons from collection tracks to retrofit staging."""

    RETROFIT_TO_WORKSHOP = 'retrofit_to_workshop'
    """Deliver wagons from retrofit staging to workshop."""

    WORKSHOP_TO_RETROFITTED = 'workshop_to_retrofitted'
    """Pick up completed wagons from workshop to retrofitted staging."""

    RETROFITTED_TO_PARKING = 'retrofitted_to_parking'
    """Move completed wagons from retrofitted staging to parking."""


class PriorityConditionType(StrEnum):
    """Types of conditions that can trigger priority changes."""

    SOURCE_FILL_ABOVE = 'source_fill_above'
    """Source track fill level exceeds threshold."""

    SOURCE_FILL_BELOW = 'source_fill_below'
    """Source track fill level is below threshold."""

    TARGET_FILL_ABOVE = 'target_fill_above'
    """Target track fill level exceeds threshold."""

    TARGET_FILL_BELOW = 'target_fill_below'
    """Target track fill level is below threshold."""

    TARGET_IDLE = 'target_idle'
    """Target resource (e.g. workshop) is idle."""


@dataclass(frozen=True)
class PriorityRule:
    """A rule that adjusts task priority based on system state.

    Parameters
    ----------
    condition : PriorityConditionType
        Type of condition to evaluate.
    threshold : float
        Threshold value for fill-level conditions (0.0-1.0).
        Ignored for non-threshold conditions like TARGET_IDLE.
    priority : int
        Priority value to apply when condition is met.
        Lower number = higher priority.
    """

    condition: PriorityConditionType
    threshold: float
    priority: int


@dataclass(frozen=True)
class HoldCondition:
    """A condition that gates task submission.

    When this condition is NOT met, the task is held back entirely —
    the coordinator will not submit it to the dispatcher. This prevents
    wasteful small-batch trips (e.g. fetching 2 wagons when target
    track is nearly full).

    Parameters
    ----------
    condition : PriorityConditionType
        Condition that must be TRUE for the task to proceed.
        E.g. TARGET_FILL_BELOW with threshold 0.6 means:
        "only submit this task when target is below 60% full."
    threshold : float
        Threshold for the condition (0.0-1.0).
    """

    condition: PriorityConditionType
    threshold: float

    def is_satisfied(self, source_fill: float, target_fill: float, target_idle: bool = False) -> bool:
        """Check if the hold condition is satisfied (task may proceed).

        Parameters
        ----------
        source_fill : float
            Fill level of source track type (0.0-1.0).
        target_fill : float
            Fill level of target track type (0.0-1.0).
        target_idle : bool
            Whether the target resource is idle.

        Returns
        -------
        bool
            True if task may proceed, False if task should be held.
        """
        match self.condition:
            case PriorityConditionType.SOURCE_FILL_ABOVE:
                return source_fill > self.threshold
            case PriorityConditionType.SOURCE_FILL_BELOW:
                return source_fill < self.threshold
            case PriorityConditionType.TARGET_FILL_ABOVE:
                return target_fill > self.threshold
            case PriorityConditionType.TARGET_FILL_BELOW:
                return target_fill < self.threshold
            case PriorityConditionType.TARGET_IDLE:
                return target_idle
        return True


@dataclass(frozen=True)
class TaskPriorityConfig:
    """Priority configuration for a single task type.

    Parameters
    ----------
    base_priority : int
        Default priority when no rules match. Lower = higher priority.
    rules : list[PriorityRule]
        Ordered list of rules. Evaluated top-to-bottom, last match wins.
    hold_until : HoldCondition | None
        If set, the task is not submitted to the dispatcher until this
        condition is satisfied. Prevents wasteful small-batch trips.
    """

    base_priority: int = 3
    rules: list[PriorityRule] = field(default_factory=list)
    hold_until: HoldCondition | None = None

    def evaluate(self, source_fill: float, target_fill: float, target_idle: bool = False) -> int:
        """Evaluate effective priority given current system state.

        Parameters
        ----------
        source_fill : float
            Fill level of source track type (0.0-1.0).
        target_fill : float
            Fill level of target track type (0.0-1.0).
        target_idle : bool
            Whether the target resource is idle.

        Returns
        -------
        int
            Effective priority (lower = more urgent).
        """
        effective = self.base_priority

        for rule in self.rules:
            if self._rule_matches(rule, source_fill, target_fill, target_idle):
                effective = rule.priority

        return effective

    @staticmethod
    def _rule_matches(rule: PriorityRule, source_fill: float, target_fill: float, target_idle: bool) -> bool:
        """Check if a rule's condition is satisfied."""
        match rule.condition:
            case PriorityConditionType.SOURCE_FILL_ABOVE:
                return source_fill > rule.threshold
            case PriorityConditionType.SOURCE_FILL_BELOW:
                return source_fill < rule.threshold
            case PriorityConditionType.TARGET_FILL_ABOVE:
                return target_fill > rule.threshold
            case PriorityConditionType.TARGET_FILL_BELOW:
                return target_fill < rule.threshold
            case PriorityConditionType.TARGET_IDLE:
                return target_idle
        return False
