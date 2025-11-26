"""Central metrics registry."""

from typing import Any

from .base import MetricCollector


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

    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record event to all collectors.

        Parameters
        ----------
        event_type : str
            Type of event.
        data : dict[str, Any]
            Event data.
        """
        for collector in self.collectors:
            collector.record_event(event_type, data)

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
                        'value': metric.value,
                        'unit': metric.unit,
                    }
                )
        return results

    def reset(self) -> None:
        """Reset all collectors."""
        for collector in self.collectors:
            collector.reset()
