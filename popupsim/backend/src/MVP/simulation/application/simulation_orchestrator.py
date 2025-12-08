"""Simulation orchestrator - replaces WorkshopOrchestrator."""

from typing import Any

from MVP.analytics.domain.events import (
    SimulationEndedEvent,
    SimulationStartedEvent,
)
from MVP.analytics.domain.value_objects.timestamp import Timestamp
from MVP.configuration.domain.models.scenario import Scenario
from MVP.simulation.domain.aggregates.simulation_session import (
    SimulationSession,
)
from MVP.simulation.domain.ports.context_port import (
    BoundedContextPort,
)
from MVP.simulation.domain.ports.simulation_engine_port import (
    SimulationEnginePort,
)


class SimulationOrchestrator:
    """Lightweight orchestrator using Simulation Context."""

    def __init__(self, engine: SimulationEnginePort, scenario: Scenario) -> None:
        self.engine = engine
        self.scenario = scenario
        self.session = SimulationSession(scenario, engine)
        self.contexts: dict[str, BoundedContextPort] = {}

    def register_context(
        self, context: BoundedContextPort, name: str | None = None
    ) -> None:
        """Register bounded context for simulation."""
        if name is None:
            name = context.__class__.__name__
        self.contexts[name] = context
        self.session.register_context(name, context)
        context.initialize(self.session)

    def run(self, until: float | None = None) -> dict[str, Any]:
        """Run simulation with all registered contexts."""
        # Fire simulation started event
        start_event = SimulationStartedEvent.create(
            timestamp=Timestamp.from_ticks(self.engine.current_time()),
            scenario_id=self.scenario.id,
            expected_duration_minutes=until or 0.0,
        )
        self._fire_event(start_event)

        # Start session
        self.session.start()

        # Start all context processes
        for context in self.contexts.values():
            context.start_processes()

        # Run simulation
        self.engine.run(until)

        # Fire simulation ended event
        end_event = SimulationEndedEvent.create(
            timestamp=Timestamp.from_ticks(self.engine.current_time()),
            scenario_id=self.scenario.id,
            completion_status="completed",
        )
        self._fire_event(end_event)

        # Stop session
        self.session.stop()

        # Collect results
        return self._collect_results()

    def _collect_results(self) -> dict[str, Any]:
        """Collect metrics from all contexts."""
        results: dict[str, Any] = {}
        for name, context in self.contexts.items():
            results[name] = context.get_metrics()
        return results

    def _fire_event(self, event: Any) -> None:
        """Fire event to all contexts that have metrics."""
        for context in self.contexts.values():
            if hasattr(context, "metrics") and context.metrics:
                context.metrics.record_event(event)
