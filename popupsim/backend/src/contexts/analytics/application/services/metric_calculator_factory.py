"""Factory for creating metric calculators."""

from typing import Any

from contexts.analytics.domain.services.capacity_metrics_calculator import (
    CapacityMetricsCalculator,
)
from contexts.analytics.domain.services.flow_metrics_calculator import (
    FlowMetricsCalculator,
)
from contexts.analytics.domain.services.locomotive_metrics_calculator import (
    LocomotiveMetricsCalculator,
)
from contexts.analytics.domain.services.shunting_metrics_calculator import (
    ShuntingMetricsCalculator,
)
from contexts.analytics.domain.services.workshop_metrics_calculator import (
    WorkshopMetricsCalculator,
)
from contexts.analytics.domain.services.yard_metrics_calculator import (
    YardMetricsCalculator,
)


class MetricCalculatorFactory:
    """Creates metric calculators."""

    def create_flow_calculator(
        self, events: list[tuple[float, Any]], event_counts: dict[str, int]
    ) -> FlowMetricsCalculator:
        return FlowMetricsCalculator(events, event_counts)

    def create_workshop_calculator(
        self, events: list[tuple[float, Any]], duration_hours: float
    ) -> WorkshopMetricsCalculator:
        return WorkshopMetricsCalculator(events, duration_hours)

    def create_locomotive_calculator(
        self, event_counts: dict[str, int]
    ) -> LocomotiveMetricsCalculator:
        return LocomotiveMetricsCalculator(event_counts)

    def create_shunting_calculator(
        self, events: list[tuple[float, Any]], event_counts: dict[str, int]
    ) -> ShuntingMetricsCalculator:
        return ShuntingMetricsCalculator(events, event_counts)

    def create_yard_calculator(
        self, event_counts: dict[str, int]
    ) -> YardMetricsCalculator:
        return YardMetricsCalculator(event_counts)

    def create_capacity_calculator(
        self, events: list[tuple[float, Any]], duration_hours: float
    ) -> CapacityMetricsCalculator:
        return CapacityMetricsCalculator(events, duration_hours)
