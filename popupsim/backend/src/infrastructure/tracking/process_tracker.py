"""Process tracker using event collector pattern."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.logging.process_logger import get_process_logger
import pandas as pd
from shared.domain.events.process_tracking_events import ProcessType
from shared.domain.events.process_tracking_events import ResourceType


@dataclass
class ProcessRecord:  # pylint: disable=too-many-instance-attributes
    """Process operation record.

    Note: Multiple attributes needed to track process details.
    """

    resource_id: str
    resource_type: ResourceType
    process_type: ProcessType
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

    def complete(self, end_time: float) -> None:
        """Complete the process."""
        self.end_time = end_time
        self.duration = end_time - self.start_time


class ProcessTracker:
    """Tracks process operations for all resources."""

    def __init__(self) -> None:
        self._active_processes: dict[str, ProcessRecord] = {}
        self._completed_processes: list[ProcessRecord] = []

    def start_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        resource_id: str,
        resource_type: ResourceType,
        process_type: ProcessType,
        location: str,
        start_time: float,
        batch_id: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Start tracking a process."""
        # Complete any existing process
        if resource_id in self._active_processes:
            self.complete_process(resource_id, start_time)

        process = ProcessRecord(
            resource_id=resource_id,
            resource_type=resource_type,
            process_type=process_type,
            location=location,
            start_time=start_time,
            batch_id=batch_id,
            additional_data=additional_data,
        )

        self._active_processes[resource_id] = process

        # Log process start
        logger = get_process_logger()
        batch_info = f' [batch={batch_id}]' if batch_id else ''
        logger.log(
            f'PROCESS_START: {resource_type.value.upper()}:{resource_id} | '
            f'{process_type.value} | {location}{batch_info}',
            sim_time=start_time,
        )

    def complete_process(self, resource_id: str, end_time: float) -> ProcessRecord | None:
        """Complete a process."""
        if resource_id not in self._active_processes:
            return None

        process = self._active_processes.pop(resource_id)
        process.complete(end_time)
        self._completed_processes.append(process)

        # Log completion
        logger = get_process_logger()
        batch_info = f' [batch={process.batch_id}]' if process.batch_id else ''
        logger.log(
            f'PROCESS_END: {process.resource_type.value.upper()}:{resource_id} | '
            f'{process.process_type.value} | {process.location} | '
            f'duration={process.duration:.1f}min{batch_info}',
            sim_time=end_time,
        )

        return process

    def get_completed_processes(self) -> list[ProcessRecord]:
        """Get all completed processes."""
        return self._completed_processes.copy()

    def get_wagon_processes(self) -> list[ProcessRecord]:
        """Get wagon processes."""
        return [p for p in self._completed_processes if p.resource_type == ResourceType.WAGON]

    def get_locomotive_processes(self) -> list[ProcessRecord]:
        """Get locomotive processes."""
        return [p for p in self._completed_processes if p.resource_type == ResourceType.LOCOMOTIVE]

    def export_to_csv(self, output_dir: Path) -> None:
        """Export process data to CSV files."""
        if not self._completed_processes:
            return

        # All processes
        all_data = []
        for process in self._completed_processes:
            all_data.append(
                {
                    'resource_id': process.resource_id,
                    'resource_type': process.resource_type.value,
                    'process_type': process.process_type.value,
                    'location': process.location,
                    'start_time': process.start_time,
                    'end_time': process.end_time,
                    'duration': process.duration,
                    'batch_id': process.batch_id or '',
                }
            )

        df = pd.DataFrame(all_data)
        df.to_csv(output_dir / 'process_tracking.csv', index=False)

        # Wagon-specific
        wagon_data = [d for d in all_data if d['resource_type'] == 'wagon']
        if wagon_data:
            wagon_df = pd.DataFrame(wagon_data)
            wagon_df.to_csv(output_dir / 'wagon_processes.csv', index=False)

        # Locomotive-specific
        loco_data = [d for d in all_data if d['resource_type'] == 'locomotive']
        if loco_data:
            loco_df = pd.DataFrame(loco_data)
            loco_df.to_csv(output_dir / 'locomotive_processes.csv', index=False)


# Global instance
_PROCESS_TRACKER: ProcessTracker | None = None


def get_process_tracker() -> ProcessTracker:
    """Get process tracker instance."""
    global _PROCESS_TRACKER  # pylint: disable=global-statement
    if _PROCESS_TRACKER is None:
        _PROCESS_TRACKER = ProcessTracker()
    return _PROCESS_TRACKER
