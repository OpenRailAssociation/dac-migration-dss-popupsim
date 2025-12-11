"""Multi-context collectors for cross-context analytics."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from contexts.analytics.domain.value_objects.metric_id import MetricId
from infrastructure.event_bus.event_bus import EventBus

from .metric_collector import MetricCollector


class ContextCollector(ABC):
    """Base class for context-specific collectors."""

    def __init__(self, context_name: str, event_bus: EventBus) -> None:
        self.context_name = context_name
        self.event_bus = event_bus
        self.collector = MetricCollector(MetricId(f'{context_name}_collector'))
        self._subscribe_to_events()

    @abstractmethod
    def _subscribe_to_events(self) -> None:
        """Subscribe to context-specific events."""


class ExternalTrainsCollector(ContextCollector):
    """Collector for External Trains Context metrics."""

    def _subscribe_to_events(self) -> None:
        """Subscribe to external trains events."""
        from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
        from shared.domain.events.wagon_lifecycle_events import WagonRetrofitCompletedEvent

        self.event_bus.subscribe(TrainArrivedEvent, self._handle_train_arrived)
        self.event_bus.subscribe(WagonRetrofitCompletedEvent, self._handle_wagon_completed)

    def _handle_train_arrived(self, event: Any) -> None:
        """Handle train arrival - compute metrics from event data."""
        current_trains = self.collector.get_latest('trains_arrived') or 0
        current_wagons = self.collector.get_latest('wagons_arrived') or 0

        self.collector.record_metric('trains_arrived', current_trains + 1)
        self.collector.record_metric('wagons_arrived', current_wagons + len(event.wagons))

    def _handle_wagon_completed(self, _event: Any) -> None:
        """Handle wagon completion - compute metrics from event data."""
        current = self.collector.get_latest('wagons_completed') or 0
        self.collector.record_metric('wagons_completed', current + 1)


class PopupRetrofitCollector(ContextCollector):
    """Collector for Popup Retrofit Context metrics."""

    def _subscribe_to_events(self) -> None:
        """Subscribe to popup retrofit events."""
        from shared.domain.events.wagon_lifecycle_events import WagonReadyForRetrofitEvent
        from shared.domain.events.wagon_lifecycle_events import WagonRetrofitCompletedEvent

        self.event_bus.subscribe(WagonReadyForRetrofitEvent, self._handle_retrofit_started)
        self.event_bus.subscribe(WagonRetrofitCompletedEvent, self._handle_retrofit_completed)

    def _handle_retrofit_started(self, _event: Any) -> None:
        """Handle retrofit start - compute metrics from event data."""
        current = self.collector.get_latest('retrofits_started') or 0
        self.collector.record_metric('retrofits_started', current + 1)

    def _handle_retrofit_completed(self, _event: Any) -> None:
        """Handle retrofit completion - compute metrics from event data."""
        current = self.collector.get_latest('retrofits_completed') or 0
        self.collector.record_metric('retrofits_completed', current + 1)


class ConfigurationCollector(ContextCollector):
    """Collector for Configuration Context metrics."""

    def _subscribe_to_events(self) -> None:
        """Subscribe to configuration events."""
        # Configuration events would be published by Configuration Context
        # For now, simplified approach since config events are less frequent

    def _handle_scenario_created(self, _event: Any) -> None:
        """Handle scenario creation - compute metrics from event data."""
        current = self.collector.get_latest('scenarios_created') or 0
        self.collector.record_metric('scenarios_created', current + 1)

    def _handle_workshop_added(self, _event: Any) -> None:
        """Handle workshop addition - compute metrics from event data."""
        current = self.collector.get_latest('workshops_added') or 0
        self.collector.record_metric('workshops_added', current + 1)


@dataclass
class MultiContextCollectorCoordinator:
    """Coordinates collection across all contexts."""

    event_bus: EventBus
    collectors: dict[str, ContextCollector] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize context collectors."""
        self.collectors = {
            'external_trains': ExternalTrainsCollector('external_trains', self.event_bus),
            'popup_retrofit': PopupRetrofitCollector('popup_retrofit', self.event_bus),
            'configuration': ConfigurationCollector('configuration', self.event_bus),
        }

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics from all contexts."""
        return {
            context_name: collector.collector.get_all_latest() for context_name, collector in self.collectors.items()
        }

    def get_context_metrics(self, context_name: str) -> dict[str, Any]:
        """Get metrics for specific context."""
        if context_name not in self.collectors:
            return {}
        return self.collectors[context_name].collector.get_all_latest()

    def clear_all_metrics(self) -> None:
        """Clear metrics from all collectors."""
        for collector in self.collectors.values():
            collector.collector.clear_metrics()
