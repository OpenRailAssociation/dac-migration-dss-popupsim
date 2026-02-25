"""Unified resource process tracker for wagons, locomotives, and other resources."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from infrastructure.logging.process_logger import get_process_logger
from shared.domain.events.unified_process_events import ProcessType
from shared.domain.events.unified_process_events import ResourceType


@dataclass
class ProcessRecord:  # pylint: disable=too-many-instance-attributes
    """Record of a resource process operation.

    Note: Multiple attributes needed to track process details.
    """

    resource_id: str
    resource_type: ResourceType
    process_type: ProcessType
    location: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None

    # Context identifiers
    batch_id: str | None = None
    rake_id: str | None = None
    locomotive_id: str | None = None
    workshop_id: str | None = None

    # Additional process data
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


class UnifiedResourceTracker:
    """Tracks processes for all resource types (wagons, locomotives, etc.)."""

    def __init__(self) -> None:
        # Active processes by resource_id
        self._active_processes: dict[str, ProcessRecord] = {}

        # Completed processes
        self._completed_processes: list[ProcessRecord] = []

        # Process history by resource_id
        self._process_history: dict[str, list[ProcessRecord]] = {}

        # Resource type mapping
        self._resource_types: dict[str, ResourceType] = {}

    def start_process(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        resource_id: str,
        resource_type: ResourceType,
        process_type: ProcessType,
        location: str,
        start_time: float,
        estimated_duration: float = 0.0,
        batch_id: str | None = None,
        rake_id: str | None = None,
        locomotive_id: str | None = None,
        workshop_id: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Start tracking a new process for any resource type."""
        # Complete any existing active process for this resource
        if resource_id in self._active_processes:
            self.complete_process(resource_id, start_time)

        # Track resource type
        self._resource_types[resource_id] = resource_type

        process = ProcessRecord(
            resource_id=resource_id,
            resource_type=resource_type,
            process_type=process_type,
            location=location,
            start_time=start_time,
            batch_id=batch_id,
            rake_id=rake_id,
            locomotive_id=locomotive_id,
            workshop_id=workshop_id,
            additional_data=additional_data,
        )

        self._active_processes[resource_id] = process

        # Initialize history if needed
        if resource_id not in self._process_history:
            self._process_history[resource_id] = []

        # Log process start
        self._log_process_start(process, estimated_duration)

    def complete_process(self, resource_id: str, end_time: float) -> ProcessRecord | None:
        """Complete the active process for a resource."""
        if resource_id not in self._active_processes:
            return None

        process = self._active_processes.pop(resource_id)
        process.complete(end_time)

        self._completed_processes.append(process)
        self._process_history[resource_id].append(process)

        # Log process completion
        self._log_process_completion(process)

        return process

    def get_active_process(self, resource_id: str) -> ProcessRecord | None:
        """Get the currently active process for a resource."""
        return self._active_processes.get(resource_id)

    def get_resource_history(self, resource_id: str) -> list[ProcessRecord]:
        """Get complete process history for a resource."""
        return self._process_history.get(resource_id, [])

    def get_processes_by_type(self, process_type: ProcessType) -> list[ProcessRecord]:
        """Get all processes of a specific type."""
        return [p for p in self._completed_processes if p.process_type == process_type]

    def get_processes_by_resource_type(self, resource_type: ResourceType) -> list[ProcessRecord]:
        """Get all processes for a specific resource type."""
        return [p for p in self._completed_processes if p.resource_type == resource_type]

    def get_processes_by_location(self, location: str) -> list[ProcessRecord]:
        """Get all processes at a specific location."""
        return [p for p in self._completed_processes if p.location == location]

    def get_locomotive_processes(self) -> list[ProcessRecord]:
        """Get all locomotive processes."""
        return self.get_processes_by_resource_type(ResourceType.LOCOMOTIVE)

    def get_wagon_processes(self) -> list[ProcessRecord]:
        """Get all wagon processes."""
        return self.get_processes_by_resource_type(ResourceType.WAGON)

    def get_comprehensive_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics across all resource types."""
        if not self._completed_processes:
            return {}

        by_resource_type: dict[str, Any] = {}
        by_process_type: dict[str, Any] = {}
        by_location: dict[str, Any] = {}

        stats: dict[str, Any] = {
            'total_processes': len(self._completed_processes),
            'active_processes': len(self._active_processes),
            'by_resource_type': by_resource_type,
            'by_process_type': by_process_type,
            'by_location': by_location,
            'resource_utilization': {},
        }

        # Group by resource type
        for resource_type in ResourceType:
            type_processes = self.get_processes_by_resource_type(resource_type)
            if type_processes:
                by_resource_type[resource_type.value] = {
                    'count': len(type_processes),
                    'avg_duration': sum(p.duration or 0 for p in type_processes) / len(type_processes),
                    'total_duration': sum(p.duration or 0 for p in type_processes),
                }

        # Group by process type
        for process_type in ProcessType:
            type_processes = self.get_processes_by_type(process_type)
            if type_processes:
                by_process_type[process_type.value] = {
                    'count': len(type_processes),
                    'avg_duration': sum(p.duration or 0 for p in type_processes) / len(type_processes),
                    'total_duration': sum(p.duration or 0 for p in type_processes),
                }

        # Group by location
        locations = {p.location for p in self._completed_processes}
        for location in locations:
            location_processes = self.get_processes_by_location(location)
            by_location[location] = {
                'count': len(location_processes),
                'avg_duration': sum(p.duration or 0 for p in location_processes) / len(location_processes),
            }

        return stats

    def export_to_json(self, output_path: Path) -> None:
        """Export all process data to JSON file."""
        completed_processes_list: list[dict[str, Any]] = []
        active_processes_list: list[dict[str, Any]] = []
        
        data: dict[str, Any] = {
            'completed_processes': completed_processes_list,
            'active_processes': active_processes_list,
            'statistics': self.get_comprehensive_statistics(),
            'resource_types': {k: v.value for k, v in self._resource_types.items()},
        }

        # Export completed processes
        for process in self._completed_processes:
            completed_processes_list.append(
                {
                    'resource_id': process.resource_id,
                    'resource_type': process.resource_type.value,
                    'process_type': process.process_type.value,
                    'location': process.location,
                    'start_time': process.start_time,
                    'end_time': process.end_time,
                    'duration': process.duration,
                    'batch_id': process.batch_id,
                    'rake_id': process.rake_id,
                    'locomotive_id': process.locomotive_id,
                    'workshop_id': process.workshop_id,
                    'additional_data': process.additional_data,
                }
            )

        # Export active processes
        for process in self._active_processes.values():
            active_processes_list.append(
                {
                    'resource_id': process.resource_id,
                    'resource_type': process.resource_type.value,
                    'process_type': process.process_type.value,
                    'location': process.location,
                    'start_time': process.start_time,
                    'batch_id': process.batch_id,
                    'rake_id': process.rake_id,
                    'locomotive_id': process.locomotive_id,
                    'workshop_id': process.workshop_id,
                    'additional_data': process.additional_data,
                }
            )

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _log_process_start(self, process: ProcessRecord, estimated_duration: float) -> None:
        """Log process start."""
        logger = get_process_logger()

        context_info: list[str] = []
        if process.batch_id:
            context_info.append(f'batch={process.batch_id}')
        if process.rake_id:
            context_info.append(f'rake={process.rake_id}')
        if process.locomotive_id:
            context_info.append(f'loco={process.locomotive_id}')
        if process.workshop_id:
            context_info.append(f'workshop={process.workshop_id}')

        context_str = f' [{", ".join(context_info)}]' if context_info else ''
        duration_str = f' est={estimated_duration:.1f}min' if estimated_duration > 0 else ''

        logger.log(
            f'PROCESS_START: {process.resource_type.value.upper()}:{process.resource_id} | '
            f'{process.process_type.value} | {process.location}{context_str}{duration_str}',
            sim_time=process.start_time,
        )

    def _log_process_completion(self, process: ProcessRecord) -> None:
        """Log process completion."""
        logger = get_process_logger()

        context_info: list[str] = []
        if process.batch_id:
            context_info.append(f'batch={process.batch_id}')
        if process.rake_id:
            context_info.append(f'rake={process.rake_id}')
        if process.locomotive_id:
            context_info.append(f'loco={process.locomotive_id}')
        if process.workshop_id:
            context_info.append(f'workshop={process.workshop_id}')

        context_str = f' [{", ".join(context_info)}]' if context_info else ''

        logger.log(
            f'PROCESS_END: {process.resource_type.value.upper()}:{process.resource_id} | '
            f'{process.process_type.value} | {process.location} | '
            f'duration={process.duration:.1f}min{context_str}',
            sim_time=process.end_time or 0.0,
        )


# Global unified tracker instance
_UNIFIED_TRACKER: UnifiedResourceTracker | None = None


def get_unified_tracker() -> UnifiedResourceTracker:
    """Get global unified resource tracker instance."""
    global _UNIFIED_TRACKER  # pylint: disable=global-statement
    if _UNIFIED_TRACKER is None:
        _UNIFIED_TRACKER = UnifiedResourceTracker()
    return _UNIFIED_TRACKER


def reset_unified_tracker() -> None:
    """Reset global unified tracker (useful for tests)."""
    global _UNIFIED_TRACKER  # pylint: disable=global-statement
    _UNIFIED_TRACKER = UnifiedResourceTracker()
