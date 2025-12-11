"""Enhanced simulation coordination infrastructure."""

from dataclasses import dataclass
import logging
from typing import Any

from infrastructure.event_bus.event_bus import EventBus
from infrastructure.event_bus.event_bus import InMemoryEventBus
from infrastructure.events.base_event import DomainEvent
from shared.infrastructure.simulation.engines.simulation_engine_port import SimulationEnginePort

logger = logging.getLogger(__name__)


@dataclass
class SimulationInfrastructure:
    """Enhanced coordination infrastructure for cross-context communication."""

    engine: SimulationEnginePort
    event_bus: EventBus

    # Wagon handoff points (SimPy Stores)
    incoming_wagons: Any  # Store - External Trains  Yard
    wagons_for_retrofit: dict[str, Any]  # Store per workshop - Yard  PopUp
    retrofitted_wagons: Any  # Store - PopUp  Yard

    @classmethod
    def create(cls, engine: SimulationEnginePort, workshop_ids: list[str] | None = None) -> 'SimulationInfrastructure':
        """Create enhanced simulation infrastructure with monitoring."""
        if workshop_ids is None:
            workshop_ids = []

        # Create enhanced event bus with simulation-specific configuration
        event_bus = InMemoryEventBus()

        # Add simulation-specific error handler
        def simulation_event_error_handler(error: Exception) -> None:
            logger.error('Simulation event error at t=%.1f: %s', engine.current_time(), error)

        event_bus.add_error_handler(simulation_event_error_handler)

        # Add simulation time logging hook
        def simulation_event_logger(event: DomainEvent) -> None:
            logger.debug('t=%.1f - %s', engine.current_time(), event.__class__.__name__)

        event_bus.add_pre_publish_hook(simulation_event_logger)

        # Configure engine hooks
        def pre_run_hook() -> None:
            logger.info(' Starting simulation at t=%.1f', engine.current_time())
            event_bus.reset_metrics()

        def post_run_hook() -> None:
            logger.info(' Simulation completed at t=%.1f', engine.current_time())
            metrics = event_bus.get_metrics()
            logger.info('Event metrics: %s', metrics)

        engine.add_pre_run_hook(pre_run_hook)
        engine.add_post_run_hook(post_run_hook)

        return cls(
            engine=engine,
            event_bus=event_bus,
            incoming_wagons=engine.create_store(),
            wagons_for_retrofit={workshop_id: engine.create_store() for workshop_id in workshop_ids},
            retrofitted_wagons=engine.create_store(),
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get infrastructure metrics."""
        return {'event_bus': self.event_bus.get_metrics(), 'engine': self.engine.get_simulation_stats()}
