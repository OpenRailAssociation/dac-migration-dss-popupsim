"""Base classes for metric collection."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class MetricResult:
    """Single metric result.

    Attributes
    ----------
    name : str
        Metric name.
    value : float | int | str
        Metric value.
    unit : str
        Unit of measurement.
    category : str
        Metric category for grouping.
    """

    name: str
    value: float | int | str
    unit: str
    category: str


class MetricCollector(ABC):
    """Base class for metric collectors.

    Collectors observe simulation events and compute metrics.
    """

    @abstractmethod
    def record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Record an event for metric computation.

        Parameters
        ----------
        event_type : str
            Type of event.
        data : dict[str, Any]
            Event data.
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
