"""SimPy event publishing adapter implementation."""

from collections.abc import Generator
from typing import Any

import simpy

from ...application.event_collector import EventCollector
from ...application.ports.event_port import EventPublishingPort
from ...domain.events import WagonJourneyEvent
from ...domain.events.batch_events import DomainEvent


class SimPyEventAdapter(EventPublishingPort):
    """SimPy implementation of event publishing."""

    def __init__(self, env: simpy.Environment, event_collector: EventCollector):
        self._env = env
        self._event_collector = event_collector

    def publish_event(self, event: DomainEvent) -> Generator[Any, Any]:
        """Publish single domain event."""
        # Handle wagon events
        if isinstance(event, WagonJourneyEvent):
            self._event_collector.add_wagon_event(event)

        # For other events, just yield control for now
        yield self._env.timeout(0)

    def publish_events(self, events: list[DomainEvent]) -> Generator[Any, Any]:
        """Publish multiple domain events."""
        for event in events:
            yield from self.publish_event(event)
