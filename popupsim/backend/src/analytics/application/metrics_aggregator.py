"""Central metrics registry."""

from typing import TYPE_CHECKING
from typing import Any

from analytics.domain.collectors.base import MetricCollector

if TYPE_CHECKING:
    from analytics.domain.events.base_event import DomainEvent


class SimulationMetrics:
    """Central metrics registry.

    Coordinates metric collection across multiple collectors.
    """

    def __init__(self) -> None:
        self.collectors: list[MetricCollector] = []
        self.collectors_by_event_type: dict[type, list[MetricCollector]] = {}

    def register(self, collector: MetricCollector) -> None:
        """Register a metric collector.

        Parameters
        ----------
        collector : MetricCollector
            Collector to register.
        """
        self.collectors.append(collector)
        for event_type in collector.handled_event_types():
            if event_type not in self.collectors_by_event_type:
                self.collectors_by_event_type[event_type] = []
            self.collectors_by_event_type[event_type].append(collector)

    def record_event(self, event: 'DomainEvent') -> None:
        """Record domain event to relevant collectors only.

        Parameters
        ----------
        event : DomainEvent
            Domain event to record.
        """
        event_type = type(event)
        collectors = self.collectors_by_event_type.get(event_type)
        if collectors:
            for collector in collectors:
                collector.record_event(event)

    def get_results(self) -> dict[str, list[dict[str, Any]]]:
        """Get all metrics grouped by category.

        Returns
        -------
        dict[str, list[dict[str, Any]]]
            Metrics grouped by category as dicts.
        """
        results: dict[str, list[dict[str, Any]]] = {}
        for collector in self.collectors:
            for metric in collector.get_results():
                if metric.category not in results:
                    results[metric.category] = []
                results[metric.category].append(
                    {
                        'name': metric.name,
                        'value': metric.value.value,
                        'unit': metric.value.unit,
                    }
                )
        return results

    def reset(self) -> None:
        """Reset all collectors."""
        for collector in self.collectors:
            collector.reset()
