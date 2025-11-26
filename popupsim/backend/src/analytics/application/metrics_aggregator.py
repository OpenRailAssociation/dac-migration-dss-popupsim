"""Central metrics registry."""

from typing import Any, TYPE_CHECKING

from analytics.domain.collectors.base import MetricCollector

if TYPE_CHECKING:
    from analytics.domain.events.base_event import DomainEvent


class SimulationMetrics:
    """Central metrics registry.

    Coordinates metric collection across multiple collectors.
    """

    def __init__(self) -> None:
        self.collectors: list[MetricCollector] = []

    def register(self, collector: MetricCollector) -> None:
        """Register a metric collector.

        Parameters
        ----------
        collector : MetricCollector
            Collector to register.
        """
        self.collectors.append(collector)

    def record_event(self, event: 'DomainEvent') -> None:
        """Record domain event to all collectors.

        Parameters
        ----------
        event : DomainEvent
            Domain event to record.
        """
        for collector in self.collectors:
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
