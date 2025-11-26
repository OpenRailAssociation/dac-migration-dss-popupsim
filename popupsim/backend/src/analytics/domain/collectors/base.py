"""Base classes for metric collection."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field

from ..events.base_event import DomainEvent
from ..value_objects.metric_value import MetricValue


@dataclass
class MetricResult:
    """Single metric result with strong typing.

    Attributes
    ----------
    name : str
        Metric name.
    value : MetricValue
        Strongly typed metric value.
    category : str
        Metric category for grouping.
    """

    name: str
    value: MetricValue
    category: str


class MetricCollector(ABC):
    """Base class for metric collectors.

    Collectors observe simulation events and compute metrics.
    """

    @abstractmethod
    def record_event(self, event: DomainEvent) -> None:
        """Record a domain event for metric computation.

        Parameters
        ----------
        event : DomainEvent
            Domain event to process.
        """
        raise NotImplementedError

    @abstractmethod
    def get_results(self) -> list[MetricResult]:
        """Get computed metrics.

        Returns
        -------
        list[MetricResult]
            List of computed metrics.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset collector state."""
        raise NotImplementedError


@dataclass
class ResourceUtilizationCollector(MetricCollector):
    """Base collector for resource utilization tracking.

    Tracks time spent in different states and calculates utilization.
    """

    resource_times: dict[str, dict[str, float]] = field(default_factory=dict)
    resource_last_event: dict[str, tuple[float, str]] = field(default_factory=dict)
    category: str = 'resource'

    def _record_state_change(self, resource_id: str, state: str, time: float) -> None:
        """Record state change for a resource."""
        if resource_id not in self.resource_times:
            self.resource_times[resource_id] = {}

        if resource_id in self.resource_last_event:
            last_time, last_state = self.resource_last_event[resource_id]
            duration = time - last_time
            self.resource_times[resource_id][last_state] = (
                self.resource_times[resource_id].get(last_state, 0.0) + duration
            )

        self.resource_last_event[resource_id] = (time, state)

    def _finalize_times(self, end_time: float) -> None:
        """Finalize all resource times at simulation end."""
        for resource_id, (last_time, last_state) in self.resource_last_event.items():
            duration = end_time - last_time
            self.resource_times[resource_id][last_state] = (
                self.resource_times[resource_id].get(last_state, 0.0) + duration
            )

    def _calculate_utilization(self) -> list[MetricResult]:
        """Calculate utilization percentages for all resources."""
        results: list[MetricResult] = []
        for resource_id, times in self.resource_times.items():
            total_time = sum(times.values())
            if total_time > 0:
                for state, time_spent in times.items():
                    utilization = (time_spent / total_time) * 100
                    results.append(
                        MetricResult(
                            f'{resource_id}_{state}_utilization',
                            MetricValue.percentage(utilization),
                            self.category,
                        )
                    )
        return results

    def reset(self) -> None:
        """Reset collector state."""
        self.resource_times.clear()
        self.resource_last_event.clear()
