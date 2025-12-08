"""Context registry for dynamic context management."""

import logging
from typing import Any

from shared.domain.events.simulation_lifecycle_events import (
    ContextInitializedEvent,
    ContextStartedEvent,
)
from shared.domain.protocols.simulation_context_protocol import (
    SimulationContextProtocol,
)

logger = logging.getLogger(__name__)


class ContextRegistry:
    """Registry for managing simulation contexts dynamically."""

    def __init__(self, event_bus: Any, engine: Any) -> None:
        self.event_bus = event_bus
        self.engine = engine
        self.contexts: dict[str, SimulationContextProtocol] = {}
        self._initialization_order: list[str] = []

    def register_context(self, name: str, context: SimulationContextProtocol) -> None:
        """Register a context for simulation."""
        if name in self.contexts:
            msg = f"Context '{name}' already registered"
            raise ValueError(msg)

        logger.info(" Registering context: %s", name)
        self.contexts[name] = context
        self._initialization_order.append(name)

    def initialize_all(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize all registered contexts in order."""
        logger.info(" Initializing %d contexts", len(self.contexts))

        for name in self._initialization_order:
            context = self.contexts[name]
            current_time = self.engine.current_time()

            logger.info(" Initializing context: %s", name)
            context.initialize(infrastructure, scenario)

            # Publish context initialized event
            event = ContextInitializedEvent.create(
                context_name=name,
                context_type=context.__class__.__name__,
                initialization_time=current_time,
            )
            self.event_bus.publish(event)

    def start_all_processes(self) -> None:
        """Start processes for all contexts."""
        for name, context in self.contexts.items():
            current_time = self.engine.current_time()
            context.start_processes()

            # Publish context started event
            event = ContextStartedEvent.create(
                context_name=name,
                processes_count=1,
                start_time=current_time,
            )
            self.event_bus.publish(event)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get metrics from all contexts."""
        metrics = {}
        for name, context in self.contexts.items():
            try:
                metrics[name] = context.get_metrics()
            except Exception as e:
                logger.exception("Failed to get metrics from %s", name)
                metrics[name] = {"error": str(e)}
        return metrics

    def get_all_status(self) -> dict[str, Any]:
        """Get status from all contexts."""
        status = {}
        for name, context in self.contexts.items():
            try:
                status[name] = context.get_status()
            except Exception as e:
                logger.exception("Failed to get status from %s", name)
                status[name] = {"status": "error", "error": str(e)}
        return status

    def cleanup_all(self) -> None:
        """Cleanup all contexts."""
        logger.info(" Cleaning up %d contexts", len(self.contexts))

        for name, context in self.contexts.items():
            try:
                context.cleanup()
                logger.debug(" Cleaned up context: %s", name)
            except Exception:
                logger.exception("Failed to cleanup %s", name)

    def broadcast_lifecycle_event(self, event: Any) -> None:
        """Broadcast lifecycle event to all contexts."""
        for name, context in self.contexts.items():
            try:
                if hasattr(event, "__class__"):
                    event_name = event.__class__.__name__
                    if event_name == "SimulationStartedEvent":
                        context.on_simulation_started(event)
                    elif event_name == "SimulationEndedEvent":
                        context.on_simulation_ended(event)
                    elif event_name == "SimulationFailedEvent":
                        context.on_simulation_failed(event)
            except Exception:
                logger.exception(
                    "Failed to broadcast %s to %s",
                    event.__class__.__name__,
                    name,
                )

    def get_context_count(self) -> int:
        """Get number of registered contexts."""
        return len(self.contexts)

    def get_context_names(self) -> list[str]:
        """Get list of registered context names."""
        return list(self.contexts.keys())
