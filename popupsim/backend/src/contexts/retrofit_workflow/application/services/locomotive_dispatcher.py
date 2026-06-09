"""Locomotive Dispatcher - priority-based task assignment for locomotives.

This module provides a central dispatcher that manages locomotive allocation
based on dynamic, fill-level-dependent task priorities. Instead of each
coordinator independently requesting a locomotive (FIFO), coordinators submit
task requests to the dispatcher, which assigns the next free locomotive to
the highest-priority pending task.
"""

from collections.abc import Callable
from collections.abc import Generator
from dataclasses import dataclass
from dataclasses import field
import logging
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.task_priority import TaskPriorityConfig
from contexts.retrofit_workflow.domain.value_objects.task_priority import TaskType
import simpy

logger = logging.getLogger(__name__)


@dataclass
class TaskRequest:
    """A request for locomotive transport submitted by a coordinator.

    Parameters
    ----------
    task_type : TaskType
        Type of transport operation.
    wagons : list[Wagon]
        Wagons to transport.
    source_track_id : str
        Track to pick up from.
    callback : simpy.Event
        SimPy event to trigger when locomotive is assigned.
    submitted_at : float
        Simulation time when task was submitted.
    target_track_id : str | None
        Target track (may be selected by dispatcher).
    metadata : dict[str, Any]
        Additional metadata for the task.
    """

    task_type: TaskType
    wagons: list[Wagon]
    source_track_id: str
    callback: simpy.Event
    submitted_at: float
    target_track_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Return string representation."""
        return f'TaskRequest(type={self.task_type.value}, wagons={len(self.wagons)}, source={self.source_track_id})'


# Mapping from TaskType to (source_track_type, target_track_type)
TASK_TRACK_TYPES: dict[TaskType, tuple[str, str]] = {
    TaskType.COLLECTION_TO_RETROFIT: ('collection', 'retrofit'),
    TaskType.RETROFIT_TO_WORKSHOP: ('retrofit', 'workshop'),
    TaskType.WORKSHOP_TO_RETROFITTED: ('workshop', 'retrofitted'),
    TaskType.RETROFITTED_TO_PARKING: ('retrofitted', 'parking'),
}


class LocomotiveDispatcher:  # pylint: disable=too-many-instance-attributes
    """Central dispatcher assigning locomotives to tasks by dynamic priority.

    The dispatcher maintains a queue of pending task requests from all
    coordinators. When a locomotive becomes available, it evaluates the
    effective priority of each pending task based on current track fill
    levels, then assigns the locomotive to the highest-priority task.

    Parameters
    ----------
    env : simpy.Environment
        SimPy simulation environment.
    locomotive_manager : Any
        LocomotiveResourceManager for allocating/releasing locomotives.
    track_selector : Any
        TrackSelectionFacade for querying track fill levels.
    priority_configs : dict[TaskType, TaskPriorityConfig]
        Priority configuration per task type.
    event_publisher : Callable | None
        Optional callback for dispatching events.

    Examples
    --------
    >>> dispatcher = LocomotiveDispatcher(env, loco_manager, track_selector, configs)
    >>> event = env.event()
    >>> dispatcher.submit_task(TaskRequest(TaskType.COLLECTION_TO_RETROFIT, wagons, 'col1', event, env.now))
    >>> loco = yield event  # Blocks until locomotive assigned
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        env: simpy.Environment,
        locomotive_manager: Any,
        track_selector: Any,
        priority_configs: dict[TaskType, TaskPriorityConfig],
        event_publisher: Callable[..., None] | None = None,
    ) -> None:
        self.env = env
        self.locomotive_manager = locomotive_manager
        self.track_selector = track_selector
        self.priority_configs = priority_configs
        self.event_publisher = event_publisher

        # Pending task requests
        self._pending: list[TaskRequest] = []

        # Signal that new tasks are available
        self._task_available: simpy.Event = env.event()

        # Metrics
        self._tasks_dispatched: int = 0
        self._total_wait_time: float = 0.0

        # Event to wake eligibility polling when new tasks arrive
        self._eligibility_wake: simpy.Event | None = None

        # Start dispatch loop
        self.env.process(self._dispatch_loop())

    def submit_task(self, task: TaskRequest) -> None:
        """Submit a task request to the dispatcher.

        The task will be queued and assigned a locomotive based on
        its effective priority relative to other pending tasks.

        Parameters
        ----------
        task : TaskRequest
            Task to enqueue for locomotive assignment.
        """
        self._pending.append(task)
        logger.info(
            't=%.1f: DISPATCHER → Task submitted: %s (pending=%d)',
            self.env.now,
            task.task_type.value,
            len(self._pending),
        )

        # Signal the dispatch loop
        if not self._task_available.triggered:
            self._task_available.succeed()

        # Wake eligibility polling if waiting (new task might be eligible)
        if self._eligibility_wake and not self._eligibility_wake.triggered:
            self._eligibility_wake.succeed()

    def _dispatch_loop(self) -> Generator[Any, Any]:
        """Dispatch locomotives to highest-priority tasks in a loop.

        Continuously waits for eligible tasks, then allocates a locomotive
        and assigns it to the highest-priority eligible task.
        """
        while True:
            # Wait for tasks to be available
            if not self._pending:
                self._task_available = self.env.event()
                yield self._task_available

            # Skip if nothing pending (shouldn't happen but defensive)
            if not self._pending:
                continue

            # Wait until at least one task is eligible before allocating a loco
            yield from self._wait_for_eligible_task()

            # Now we know there's an eligible task — allocate a locomotive
            loco = yield self.env.process(self.locomotive_manager.allocate(purpose='dispatcher'))

            # Select best eligible task (re-evaluate after loco wait)
            best_task = self._select_best_task()

            if best_task is None:
                # Edge case: task became ineligible while waiting for loco
                yield self.env.process(self.locomotive_manager.release(loco, purpose='dispatcher'))
                continue

            # Assign locomotive to the winning task
            wait_time = self.env.now - best_task.submitted_at
            self._total_wait_time += wait_time
            self._tasks_dispatched += 1

            logger.info(
                't=%.1f: DISPATCHER → Assigned loco %s to %s (waited %.1f min, pending=%d)',
                self.env.now,
                loco.id,
                best_task.task_type.value,
                wait_time,
                len(self._pending),
            )

            # Trigger the callback event with the locomotive
            best_task.callback.succeed(value=loco)

            # If more tasks pending, re-trigger the loop immediately
            if self._pending and not self._task_available.triggered:
                self._task_available.succeed()

    def _wait_for_eligible_task(self) -> Generator[Any, Any]:
        """Wait until at least one pending task passes its hold_until check.

        Uses a polling interval to periodically re-check hold conditions,
        since fill levels change as other operations complete. Also wakes
        up when new tasks are submitted (they might be immediately eligible).
        """
        poll_interval = 5.0  # Re-check every 5 sim minutes

        while True:
            # Check if any pending task is eligible right now
            for task in self._pending:
                if self._is_task_eligible(task):
                    return

            # None eligible — wait for either a new task or the poll interval
            new_task_event = self.env.event()
            self._eligibility_wake = new_task_event
            timeout_event = self.env.timeout(poll_interval)

            # Yield on whichever fires first
            yield new_task_event | timeout_event
            self._eligibility_wake = None

    def _select_best_task(self) -> TaskRequest | None:
        """Select the highest-priority pending task that is eligible to run.

        Evaluates effective priority for each pending task based on
        current track fill levels, then returns the most urgent one.
        Tasks whose hold_until condition is not met are skipped.
        Ties are broken by submission time (FIFO).

        Returns
        -------
        TaskRequest | None
            Highest priority eligible task, or None if all are held/empty.
        """
        if not self._pending:
            return None

        best_task: TaskRequest | None = None
        best_score: tuple[int, float] | None = None  # (priority, submitted_at)

        for task in self._pending:
            # Check hold_until gate
            if not self._is_task_eligible(task):
                continue

            priority = self._evaluate_task_priority(task)
            score = (priority, task.submitted_at)

            if best_score is None or score < best_score:
                best_score = score
                best_task = task

        if best_task:
            self._pending.remove(best_task)

        return best_task

    def _is_task_eligible(self, task: TaskRequest) -> bool:
        """Check if a task's hold_until condition allows it to proceed.

        A task is eligible if:
        - It has no hold_until condition, OR
        - Its hold_until condition is satisfied, OR
        - It has exceeded its max_hold_time (escape hatch)

        Parameters
        ----------
        task : TaskRequest
            Task to check eligibility for.

        Returns
        -------
        bool
            True if the task may proceed, False if it should be held back.
        """
        config = self.priority_configs.get(task.task_type)
        if config is None or config.hold_until is None:
            return True

        # Escape hatch: override hold if task has waited too long
        if config.max_hold_time is not None:
            wait_time = self.env.now - task.submitted_at
            if wait_time >= config.max_hold_time:
                logger.info(
                    't=%.1f: DISPATCHER → Hold override for %s (waited %.1f min >= max %.1f min)',
                    self.env.now,
                    task.task_type.value,
                    wait_time,
                    config.max_hold_time,
                )
                return True

        source_fill, target_fill, target_idle = self._get_fill_levels(task.task_type)
        return config.hold_until.is_satisfied(source_fill, target_fill, target_idle)

    def _evaluate_task_priority(self, task: TaskRequest) -> int:
        """Evaluate effective priority for a task given current state.

        Parameters
        ----------
        task : TaskRequest
            Task to evaluate.

        Returns
        -------
        int
            Effective priority (lower = more urgent).
        """
        config = self.priority_configs.get(task.task_type)
        if config is None:
            return 5  # Low default priority for unknown task types

        # Get track fill levels for this task type
        source_fill, target_fill, target_idle = self._get_fill_levels(task.task_type)

        return config.evaluate(source_fill, target_fill, target_idle)

    def _get_fill_levels(self, task_type: TaskType) -> tuple[float, float, bool]:
        """Get current fill levels for source and target track types.

        Parameters
        ----------
        task_type : TaskType
            Task type to look up track types for.

        Returns
        -------
        tuple[float, float, bool]
            (source_fill_ratio, target_fill_ratio, target_is_idle)
        """
        track_types = TASK_TRACK_TYPES.get(task_type)
        if not track_types or not self.track_selector:
            return 0.0, 0.0, False

        source_type, target_type = track_types

        source_fill = self._get_type_fill_ratio(source_type)
        target_fill = self._get_type_fill_ratio(target_type)

        # Check if target is idle (workshop-specific)
        target_idle = False
        if target_type == 'workshop' and target_fill < 0.05:
            target_idle = True

        return source_fill, target_fill, target_idle

    def _get_type_fill_ratio(self, track_type: str) -> float:
        """Get average fill ratio for a track type.

        Parameters
        ----------
        track_type : str
            Track type to query.

        Returns
        -------
        float
            Average fill ratio (0.0-1.0) across all tracks of this type.
        """
        if not self.track_selector:
            return 0.0

        tracks = self.track_selector.tracks_by_type.get(track_type, [])
        if not tracks:
            return 0.0

        total_capacity = 0.0
        total_occupied = 0.0

        for track in tracks:
            total_capacity += track.capacity_meters
            total_occupied += track.get_occupied_capacity()

        if total_capacity == 0:
            return 0.0

        return total_occupied / total_capacity

    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        return len(self._pending)

    def get_metrics(self) -> dict[str, Any]:
        """Get dispatcher metrics.

        Returns
        -------
        dict[str, Any]
            Metrics including dispatched count, average wait, pending tasks.
        """
        avg_wait = self._total_wait_time / self._tasks_dispatched if self._tasks_dispatched > 0 else 0.0
        return {
            'tasks_dispatched': self._tasks_dispatched,
            'pending_tasks': len(self._pending),
            'average_wait_time': avg_wait,
        }
