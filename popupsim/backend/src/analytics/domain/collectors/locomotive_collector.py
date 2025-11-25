"""Locomotive utilization metrics collector."""

from dataclasses import dataclass
from typing import Any

from .base import MetricResult
from .base import ResourceUtilizationCollector


@dataclass
class LocomotiveCollector(ResourceUtilizationCollector):
    """Collect locomotive utilization metrics.

    Tracks locomotive status changes and calculates time spent in each state.
    """

    category: str = 'locomotive'

    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record locomotive events."""
        if event_type == 'locomotive_status_change':
            loco_id = data.get('locomotive_id')
            status = data.get('status')
            time = data.get('time', 0.0)
            if loco_id and status:
                self._record_state_change(loco_id, status, time)

        elif event_type == 'simulation_end':
            end_time = data.get('time', 0.0)
            self._finalize_times(end_time)

    def get_results(self) -> list[MetricResult]:
        """Get locomotive utilization metrics."""
        return self._calculate_utilization()
