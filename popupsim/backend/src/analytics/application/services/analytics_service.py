"""Analytics Service - orchestrates analytics with observer pattern."""

import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon

from configuration.domain.models.scenario import Scenario

from ...domain.aggregates.analytics_session import AnalyticsSession
from ...domain.factories.analytics_factory import AnalyticsFactory
from ...domain.models.kpi_result import KPIResult
from ...domain.observers.analytics_observer import KPIObserver
from ...domain.observers.analytics_observer import MetricsObserver
from ...domain.observers.event_publisher import EventPublisher
from ...domain.services.kpi_calculator import KPICalculator

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics with observer pattern integration."""

    def __init__(self) -> None:
        """Initialize analytics service."""
        self.publisher = EventPublisher()
        self.kpi_observer = KPIObserver()
        self.metrics_observer = MetricsObserver()
        self.kpi_calculator = KPICalculator()

        # Subscribe observers
        self.publisher.subscribe(self.kpi_observer)
        self.publisher.subscribe(self.metrics_observer)

    def start_analytics_session(self, scenario: Scenario) -> AnalyticsSession:
        """Start analytics session and publish simulation started event."""
        session = AnalyticsFactory.create_analytics_session(scenario.scenario_id)

        # Publish simulation started event
        event = AnalyticsFactory.create_simulation_started_event(scenario)
        self.publisher.publish(event)
        session.add_event(event)

        logger.info('Started analytics session for scenario %s', scenario.scenario_id)
        return session

    def record_wagon_delivered(self, session: AnalyticsSession, wagon: Wagon) -> None:
        """Record wagon delivered event."""
        event = AnalyticsFactory.create_wagon_delivered_event(wagon)
        self.publisher.publish(event)
        session.add_event(event)

    def record_wagon_retrofitted(self, session: AnalyticsSession, wagon: Wagon, workshop_id: str) -> None:
        """Record wagon retrofitted event."""
        event = AnalyticsFactory.create_wagon_retrofitted_event(wagon, workshop_id)
        self.publisher.publish(event)
        session.add_event(event)

    def record_wagon_rejected(self, session: AnalyticsSession, wagon: Wagon, reason: str) -> None:
        """Record wagon rejected event."""
        event = AnalyticsFactory.create_wagon_rejected_event(wagon, reason)
        self.publisher.publish(event)
        session.add_event(event)

    def complete_analytics_session(
        self,
        session: AnalyticsSession,
        scenario: Scenario,
        simulation_data: dict[str, Any],
        metrics: dict[str, list[dict[str, Any]]],
    ) -> KPIResult:
        """Complete analytics session and calculate final KPIs.

        Parameters
        ----------
        session : AnalyticsSession
            The analytics session to complete.
        scenario : Scenario
            The simulation scenario.
        simulation_data : dict[str, Any]
            Dictionary containing 'wagons', 'rejected_wagons', and 'workshops' keys.
        metrics : dict[str, list[dict[str, Any]]]
            Collected simulation metrics.
        """
        wagons = simulation_data['wagons']
        rejected_wagons = simulation_data['rejected_wagons']
        workshops = simulation_data['workshops']

        # Publish simulation completed event
        event = AnalyticsFactory.create_simulation_completed_event(
            scenario.scenario_id, len(wagons), len(rejected_wagons)
        )
        self.publisher.publish(event)
        session.add_event(event)

        # Calculate KPIs using collected events and metrics
        kpi_result = self.kpi_calculator.calculate_from_simulation(
            metrics, scenario, wagons, rejected_wagons, workshops
        )

        session.complete_session()
        logger.info('Completed analytics session for scenario %s', scenario.scenario_id)

        return kpi_result

    def get_collected_events(self) -> list[Any]:
        """Get all collected events from KPI observer."""
        return self.kpi_observer.get_events()

    def get_collected_metrics(self) -> dict[str, list[Any]]:
        """Get all collected metrics from metrics observer."""
        return self.metrics_observer.get_all_metrics()

    def clear_observers(self) -> None:
        """Clear all observer data."""
        self.kpi_observer.clear_events()
        self.metrics_observer.clear_metrics()

    def add_observer(self, observer: Any) -> None:
        """Add custom observer."""
        self.publisher.subscribe(observer)

    def remove_observer(self, observer: Any) -> None:
        """Remove custom observer."""
        self.publisher.unsubscribe(observer)
