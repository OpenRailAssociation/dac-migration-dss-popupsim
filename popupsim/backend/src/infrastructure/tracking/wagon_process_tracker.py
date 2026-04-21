"""Wagon process tracker for detailed operation monitoring."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from infrastructure.logging.process_logger import get_process_logger


@dataclass
class ProcessRecord:  # pylint: disable=too-many-instance-attributes
    """Record of a wagon process operation.

    Note: Multiple attributes needed to track wagon process details.
    """

    wagon_id: str
    process_type: str
    location: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    batch_id: str | None = None
    additional_data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.additional_data is None:
            self.additional_data = {}

    @property
    def is_completed(self) -> bool:
        """Check if process is completed."""
        return self.end_time is not None

    def complete(self, end_time: float) -> None:
        """Mark process as completed."""
        self.end_time = end_time
        self.duration = end_time - self.start_time


class WagonProcessTracker:
    """Tracks all wagon processes for detailed analysis."""

    def __init__(self) -> None:
        self._active_processes: dict[str, ProcessRecord] = {}  # wagon_id -> active process
        self._completed_processes: list[ProcessRecord] = []
        self._process_history: dict[str, list[ProcessRecord]] = {}  # wagon_id -> process list

    def start_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        wagon_id: str,
        process_type: str,
        location: str,
        start_time: float,
        batch_id: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Start tracking a new process."""
        # Complete any existing active process for this wagon
        if wagon_id in self._active_processes:
            self.complete_process(wagon_id, start_time)

        process = ProcessRecord(
            wagon_id=wagon_id,
            process_type=process_type,
            location=location,
            start_time=start_time,
            batch_id=batch_id,
            additional_data=additional_data,
        )

        self._active_processes[wagon_id] = process

        # Initialize history if needed
        if wagon_id not in self._process_history:
            self._process_history[wagon_id] = []

        # Log process start
        logger = get_process_logger()
        batch_info = f' [batch={batch_id}]' if batch_id else ''
        additional_info = ''
        if additional_data:
            additional_info = f' {additional_data}'

        logger.log(
            f'PROCESS_START: {wagon_id} | {process_type} | {location}{batch_info}{additional_info}', sim_time=start_time
        )

    def complete_process(self, wagon_id: str, end_time: float) -> ProcessRecord | None:
        """Complete the active process for a wagon."""
        if wagon_id not in self._active_processes:
            return None

        process = self._active_processes.pop(wagon_id)
        process.complete(end_time)

        self._completed_processes.append(process)
        self._process_history[wagon_id].append(process)

        # Log process completion
        logger = get_process_logger()
        batch_info = f' [batch={process.batch_id}]' if process.batch_id else ''
        logger.log(
            f'PROCESS_END: {wagon_id} | {process.process_type} | {process.location} | '
            f'duration={process.duration:.1f}min{batch_info}',
            sim_time=end_time,
        )

        return process

    def get_active_process(self, wagon_id: str) -> ProcessRecord | None:
        """Get the currently active process for a wagon."""
        return self._active_processes.get(wagon_id)

    def get_wagon_history(self, wagon_id: str) -> list[ProcessRecord]:
        """Get complete process history for a wagon."""
        return self._process_history.get(wagon_id, [])

    def get_all_processes(self) -> list[ProcessRecord]:
        """Get all completed processes."""
        return self._completed_processes.copy()

    def get_processes_by_type(self, process_type: str) -> list[ProcessRecord]:
        """Get all processes of a specific type."""
        return [p for p in self._completed_processes if p.process_type == process_type]

    def get_processes_by_location(self, location: str) -> list[ProcessRecord]:
        """Get all processes at a specific location."""
        return [p for p in self._completed_processes if p.location == location]

    def get_active_processes_count(self) -> int:
        """Get count of currently active processes."""
        return len(self._active_processes)

    def get_process_statistics(self) -> dict[str, Any]:
        """Get comprehensive process statistics."""
        if not self._completed_processes:
            return {}

        by_type: dict[str, Any] = {}
        by_location: dict[str, int] = {}

        stats: dict[str, Any] = {
            'total_processes': len(self._completed_processes),
            'active_processes': len(self._active_processes),
            'by_type': by_type,
            'by_location': by_location,
            'duration_stats': {},
        }

        # Group by process type
        for process in self._completed_processes:
            process_type = process.process_type
            if process_type not in by_type:
                by_type[process_type] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'avg_duration': 0.0,
                    'min_duration': float('inf'),
                    'max_duration': 0.0,
                }

            type_stats = by_type[process_type]
            type_stats['count'] += 1
            type_stats['total_duration'] += process.duration or 0.0
            type_stats['min_duration'] = min(type_stats['min_duration'], process.duration or 0.0)
            type_stats['max_duration'] = max(type_stats['max_duration'], process.duration or 0.0)

        # Calculate averages
        for type_stats in by_type.values():
            if type_stats['count'] > 0:
                type_stats['avg_duration'] = type_stats['total_duration'] / type_stats['count']
                if type_stats['min_duration'] == float('inf'):
                    type_stats['min_duration'] = 0.0

        # Group by location
        for process in self._completed_processes:
            location = process.location
            if location not in by_location:
                by_location[location] = 0
            by_location[location] += 1

        return stats

    def export_to_json(self, output_path: Path) -> None:
        """Export all process data to JSON file."""
        completed_list: list[dict[str, Any]] = []
        active_list: list[dict[str, Any]] = []

        data: dict[str, Any] = {
            'completed_processes': completed_list,
            'active_processes': active_list,
            'statistics': self.get_process_statistics(),
        }

        # Export completed processes
        for process in self._completed_processes:
            completed_list.append(
                {
                    'wagon_id': process.wagon_id,
                    'process_type': process.process_type,
                    'location': process.location,
                    'start_time': process.start_time,
                    'end_time': process.end_time,
                    'duration': process.duration,
                    'batch_id': process.batch_id,
                    'additional_data': process.additional_data,
                }
            )

        # Export active processes
        for process in self._active_processes.values():
            active_list.append(
                {
                    'wagon_id': process.wagon_id,
                    'process_type': process.process_type,
                    'location': process.location,
                    'start_time': process.start_time,
                    'batch_id': process.batch_id,
                    'additional_data': process.additional_data,
                }
            )

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Global process tracker instance
_PROCESS_TRACKER: WagonProcessTracker | None = None


def get_process_tracker() -> WagonProcessTracker:
    """Get global process tracker instance."""
    global _PROCESS_TRACKER  # pylint: disable=global-statement
    if _PROCESS_TRACKER is None:
        _PROCESS_TRACKER = WagonProcessTracker()
    return _PROCESS_TRACKER


def reset_process_tracker() -> None:
    """Reset global process tracker (useful for tests)."""
    global _PROCESS_TRACKER  # pylint: disable=global-statement
    _PROCESS_TRACKER = WagonProcessTracker()
