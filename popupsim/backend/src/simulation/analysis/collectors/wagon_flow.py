"""Wagon flow metrics collector."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from ..base import MetricCollector
from ..base import MetricResult


@dataclass
class WagonFlowCollector(MetricCollector):
    """Collect wagon flow metrics.

    Tracks wagon delivery, retrofit completion, and flow times.
    """

    wagons_delivered: int = 0
    wagons_retrofitted: int = 0
    wagons_rejected: int = 0
    total_flow_time: float = 0.0
    wagon_start_times: dict[str, float] = field(default_factory=dict)

    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record wagon flow events."""
        if event_type == 'wagon_delivered':
            self.wagons_delivered += 1
            wagon_id = data.get('wagon_id')
            time = data.get('time', 0.0)
            if wagon_id:
                self.wagon_start_times[wagon_id] = time

        elif event_type == 'wagon_retrofitted':
            self.wagons_retrofitted += 1
            wagon_id = data.get('wagon_id')
            time = data.get('time', 0.0)
            if wagon_id and wagon_id in self.wagon_start_times:
                flow_time = time - self.wagon_start_times[wagon_id]
                self.total_flow_time += flow_time

        elif event_type == 'wagon_rejected':
            self.wagons_rejected += 1

    def get_results(self) -> list[MetricResult]:
        """Get wagon flow metrics."""
        avg_flow_time = self.total_flow_time / self.wagons_retrofitted if self.wagons_retrofitted > 0 else 0.0

        return [
            MetricResult('wagons_delivered', self.wagons_delivered, 'wagons', 'wagon_flow'),
            MetricResult('wagons_retrofitted', self.wagons_retrofitted, 'wagons', 'wagon_flow'),
            MetricResult('wagons_rejected', self.wagons_rejected, 'wagons', 'wagon_flow'),
            MetricResult('avg_flow_time', round(avg_flow_time, 1), 'min', 'wagon_flow'),
        ]

    def reset(self) -> None:
        """Reset collector state."""
        self.wagons_delivered = 0
        self.wagons_retrofitted = 0
        self.wagons_rejected = 0
        self.total_flow_time = 0.0
        self.wagon_start_times.clear()
