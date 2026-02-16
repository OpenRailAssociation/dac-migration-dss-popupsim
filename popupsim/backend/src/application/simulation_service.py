"""Enhanced simulation application service with context registry and lifecycle events."""

from dataclasses import dataclass
import logging
from typing import Any

from application.context_registry import ContextRegistry
from contexts.configuration.application.configuration_context import ConfigurationContext
from contexts.configuration.domain.models.scenario import Scenario
from contexts.external_trains.application.external_trains_context import ExternalTrainsContext
from contexts.railway_infrastructure.infrastructure.di_container import create_railway_context
from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
from shared.domain.events.simulation_lifecycle_events import SimulationEndedEvent
from shared.domain.events.simulation_lifecycle_events import SimulationFailedEvent
from shared.domain.events.simulation_lifecycle_events import SimulationStartedEvent
from shared.infrastructure.simulation.coordination.simulation_infrastructure import SimulationInfrastructure
from shared.infrastructure.simulation.engines.simpy_adapter import SimPyEngineAdapter

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Result of simulation execution."""

    metrics: dict[str, Any]
    duration: float
    success: bool


class SimulationApplicationService:
    """Application service managing simulation lifecycle."""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.engine = SimPyEngineAdapter.create()

        # Extract workshop IDs for infrastructure
        workshop_ids = [w.id for w in (scenario.workshops or [])]
        self.infra = SimulationInfrastructure.create(self.engine, workshop_ids)

        # Create context registry for dynamic context management
        self.context_registry = ContextRegistry(self.infra.event_bus, self.engine)
        self.contexts: dict[str, Any] = {}  # Keep for backward compatibility
        self._rake_registry = None

    def execute(self, until: float) -> SimulationResult:
        """Execute simulation with enhanced lifecycle management and events."""
        start_time = self.engine.current_time()

        try:
            # Initialize contexts
            self._initialize_contexts()

            # Publish simulation started event
            started_event = SimulationStartedEvent.create(
                scenario_id=self.scenario.id,
                expected_duration=until,
                contexts_count=self.context_registry.get_context_count(),
            )
            self.infra.event_bus.publish(started_event)
            self.context_registry.broadcast_lifecycle_event(started_event)

            logger.info(
                ' Starting simulation for scenario %s (until=%s)',
                self.scenario.id,
                until,
            )

            # Start processes
            self._start_processes()

            # Run simulation
            self.engine.run(until)

            # Check if simulation ended early
            actual_time = self.engine.current_time()
            if actual_time < until:
                logger.warning(
                    (
                        '⚠️  Simulation ended early at t=%.1f (expected t=%.1f) -'
                        ' likely deadlock or all processes completed'
                    ),
                    actual_time,
                    until,
                )

            # Collect results
            result = self._collect_results(self.engine.current_time() - start_time)

            # Publish simulation ended event
            ended_event = SimulationEndedEvent.create(
                scenario_id=self.scenario.id,
                actual_duration=self.engine.current_time() - start_time,
                completion_status='completed',
                final_metrics=result.metrics,
            )
            self.infra.event_bus.publish(ended_event)
            self.context_registry.broadcast_lifecycle_event(ended_event)

            logger.info(' Simulation completed successfully for scenario %s', self.scenario.id)
            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            failure_time = self.engine.current_time()
            logger.exception(' Simulation failed for scenario %s: %s', self.scenario.id, e)

            # Publish simulation failed event
            failed_event = SimulationFailedEvent.create(
                scenario_id=self.scenario.id,
                error_message=str(e),
                failure_time=failure_time,
                context_states=self.context_registry.get_all_status(),
            )
            self.infra.event_bus.publish(failed_event)
            self.context_registry.broadcast_lifecycle_event(failed_event)

            # Cleanup contexts
            self.context_registry.cleanup_all()

            return SimulationResult(metrics={}, duration=failure_time - start_time, success=False)

    def get_current_time(self) -> float:
        """Return the current time.

        Returns
        -------
        float
            Current time
        """
        return self.infra.engine.current_time()

    def _initialize_contexts(self) -> None:
        """Initialize all bounded contexts."""
        logger.info(' Initializing contexts for scenario %s', self.scenario.id)

        # Create and initialize retrofit context
        retrofit_context = RetrofitWorkshopContext(
            self.engine.get_env(),
            self.scenario,
        )
        retrofit_context.initialize()
        self.contexts['retrofit_workflow'] = retrofit_context

        # Subscribe to train arrivals
        retrofit_context.subscribe_to_train_arrivals(self.infra.event_bus)

        # Register shared contexts
        self._register_shared_contexts()

        # Initialize shared contexts
        self.context_registry.initialize_all(self.infra, self.scenario)

    def _register_shared_contexts(self) -> None:
        """Register contexts shared by both workflows."""
        # Configuration Context
        config_context = ConfigurationContext(self.infra.event_bus)
        config_context.finalize_scenario(self.scenario.id)
        self.context_registry.register_context('configuration', config_context)
        self.contexts['configuration'] = config_context

        # Railway Infrastructure Context (needed for track management)
        railway_context = create_railway_context(self.scenario)
        self.context_registry.register_context('railway', railway_context)
        self.contexts['railway'] = railway_context

        # External Trains Context
        external_trains_context = ExternalTrainsContext(self.infra.event_bus)
        self.context_registry.register_context('external_trains', external_trains_context)
        self.contexts['external_trains'] = external_trains_context



    def _start_processes(self) -> None:
        """Start all context processes."""
        logger.info(' Starting processes for all contexts')

        # Start all context processes through registry
        self.context_registry.start_all_processes()

        # Start retrofit workflow
        logger.info(' Starting retrofit workflow processes')
        self.contexts['retrofit_workflow'].start_processes()

        # Start main simulation orchestration process
        self.engine.schedule_process(self._orchestrate_simulation())



    def _collect_results(self, duration: float) -> SimulationResult:
        """Collect results from all contexts using registry."""
        logger.info(' Collecting results from all contexts')

        # Get metrics from all contexts through registry
        all_metrics = self.context_registry.get_all_metrics()

        # Add infrastructure metrics
        all_metrics['infrastructure'] = self.infra.get_metrics()

        return SimulationResult(metrics=all_metrics, duration=duration, success=True)

    def _orchestrate_simulation(self) -> Any:
        """Orchestrate main simulation process."""
        # External Trains Context handles wagon creation and train arrivals
        # Just wait for simulation to complete
        yield from self.engine.delay(0)
