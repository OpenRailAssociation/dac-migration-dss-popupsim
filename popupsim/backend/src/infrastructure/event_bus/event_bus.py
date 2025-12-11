"""Enhanced event bus interface and implementation."""

from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
import logging
from typing import Any

from infrastructure.events.base_event import DomainEvent

logger = logging.getLogger(__name__)


@dataclass
class EventMetrics:
    """Event bus metrics."""

    events_published: int = 0
    events_processed: int = 0
    handler_errors: int = 0
    subscribers_count: int = 0
    event_types_count: int = 0


class EventBus(ABC):
    """Abstract event bus interface."""

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish event to subscribers."""

    @abstractmethod
    def subscribe(self, event_type: type, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe handler to event type."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get event bus metrics."""

    @abstractmethod
    def add_error_handler(self, handler: Callable[[Exception, DomainEvent], None]) -> None:
        """Add global error handler."""


class InMemoryEventBus(EventBus):
    """Enhanced in-memory event bus with monitoring and error handling."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[DomainEvent], None]]] = defaultdict(list)
        self._metrics = EventMetrics()
        self._event_history: list[tuple[datetime, DomainEvent]] = []
        self._error_handlers: list[Callable[[Exception, DomainEvent], None]] = []
        self._pre_publish_hooks: list[Callable[[DomainEvent], None]] = []
        self._post_publish_hooks: list[Callable[[DomainEvent], None]] = []

    def publish(self, event: DomainEvent) -> None:
        """Publish event with monitoring and error handling."""
        self._metrics.events_published += 1
        self._event_history.append((datetime.now(UTC), event))

        # Execute pre-publish hooks
        for hook in self._pre_publish_hooks:
            try:
                hook(event)
            except Exception:
                logger.exception('Pre-publish hook error')

        # Log event with context
        event_data = self._extract_event_data(event)
        logger.info('EVENT_PUBLISHED: %s | %s', event.__class__.__name__, event_data)

        handlers = self._subscribers[type(event)]
        if not handlers:
            logger.warning('EVENT_NO_SUBSCRIBERS: %s', event.__class__.__name__)
            return

        # Execute handlers with error handling
        for handler in handlers:
            try:
                handler_context = self._get_handler_context(handler)
                logger.info(
                    'EVENT_HANDLING: %s -> %s',
                    event.__class__.__name__,
                    handler_context,
                )
                handler(event)
                self._metrics.events_processed += 1
                logger.info('EVENT_HANDLED: %s by %s', event.__class__.__name__, handler_context)
            except Exception as e:
                self._metrics.handler_errors += 1
                logger.exception(
                    'EVENT_ERROR: %s in %s',
                    event.__class__.__name__,
                    self._get_handler_context(handler),
                )

                # Execute error handlers
                for error_handler in self._error_handlers:
                    try:
                        error_handler(e, event)
                    except Exception:
                        logger.exception('Error handler failed')

        # Execute post-publish hooks
        for hook in self._post_publish_hooks:
            try:
                hook(event)
            except Exception:
                logger.exception('Post-publish hook error')

    def subscribe(self, event_type: type, handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe handler with monitoring."""
        self._subscribers[event_type].append(handler)
        self._metrics.subscribers_count += 1

        if len(self._subscribers[event_type]) == 1:
            self._metrics.event_types_count += 1

        handler_context = self._get_handler_context(handler)
        logger.info(
            'EVENT_SUBSCRIBED: %s -> %s (total: %d)',
            event_type.__name__,
            handler_context,
            len(self._subscribers[event_type]),
        )

    def add_error_handler(self, handler: Callable[[Exception, DomainEvent], None]) -> None:
        """Add global error handler."""
        self._error_handlers.append(handler)

    def add_pre_publish_hook(self, hook: Callable[[DomainEvent], None]) -> None:
        """Add pre-publish hook."""
        self._pre_publish_hooks.append(hook)

    def add_post_publish_hook(self, hook: Callable[[DomainEvent], None]) -> None:
        """Add post-publish hook."""
        self._post_publish_hooks.append(hook)

    def get_metrics(self) -> dict[str, Any]:
        """Get event bus metrics."""
        return {
            'events_published': self._metrics.events_published,
            'events_processed': self._metrics.events_processed,
            'handler_errors': self._metrics.handler_errors,
            'subscribers_count': self._metrics.subscribers_count,
            'event_types_count': self._metrics.event_types_count,
            'error_rate': self._metrics.handler_errors / max(1, self._metrics.events_processed),
        }

    def get_event_history(self, limit: int = 100) -> list[tuple[datetime, str]]:
        """Get recent event history."""
        return [(timestamp, event.__class__.__name__) for timestamp, event in self._event_history[-limit:]]

    def get_subscriber_stats(self) -> dict[str, int]:
        """Get subscriber statistics by event type."""
        return {event_type.__name__: len(handlers) for event_type, handlers in self._subscribers.items()}

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self._metrics = EventMetrics()

    def _get_handler_context(self, handler: Callable) -> str:
        """Extract context information from handler."""
        if hasattr(handler, '__self__'):
            return f'{handler.__self__.__class__.__name__}.{handler.__name__}'
        return handler.__name__

    def _extract_event_data(self, event: DomainEvent) -> str:
        """Extract relevant data from event for logging."""
        data_parts = []
        if hasattr(event, 'wagon_id'):
            data_parts.append(f'wagon={event.wagon_id}')
        if hasattr(event, 'train_id'):
            data_parts.append(f'train={event.train_id}')
        if hasattr(event, 'workshop_id'):
            data_parts.append(f'workshop={event.workshop_id}')
        if hasattr(event, 'rake_id'):
            data_parts.append(f'rake={event.rake_id}')
        if hasattr(event, 'event_timestamp'):
            data_parts.append(f'time={event.event_timestamp:.1f}')
        return ' | '.join(data_parts) if data_parts else 'no_data'
