"""Enhanced simulation application service with context registry and lifecycle events.

Todo
-----
    Check if te context registry is still needed or can be removed. The
    implementation was used by the old version.
"""

from dataclasses import dataclass
import logging
from typing import Any

from application.context_registry import ContextRegistry
from contexts.analytics.application.analytics_context import AnalyticsContext
from contexts.analytics.infrastructure.repositories.in_memory_analytics_repository import InMemoryAnalyticsRepository
from contexts.configuration.application.configuration_context import ConfigurationContext
from contexts.configuration.domain.models.scenario import Scenario
from contexts.external_trains.application.external_trains_context import ExternalTrainsContext
from contexts.popup_retrofit.application.popup_context import PopUpRetrofitContext
from contexts.railway_infrastructure.application.railway_context import RailwayInfrastructureContext
from contexts.shunting_operations.application.shunting_context import ShuntingOperationsContext
from contexts.yard_operations.application.yard_context import YardOperationsContext
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

            # Collect results
            result = self._collect_results(until)

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
        """Initialize all bounded contexts using registry."""
        logger.info(' Initializing contexts for scenario %s', self.scenario.id)

        # Register all contexts with the registry
        self._register_all_contexts()

        # Add cross-context references BEFORE initialization
        self.infra.contexts = self.contexts
        self.infra.shunting_context = self.contexts.get('shunting')

        # Initialize all contexts through registry
        self.context_registry.initialize_all(self.infra, self.scenario)

        # Setup workshop infrastructure
        self._setup_workshop_infrastructure()

    def _register_all_contexts(self) -> None:
        """Register all bounded contexts with the registry."""
        # Initialize Configuration Context (static configuration)
        config_context = ConfigurationContext(self.infra.event_bus)

        config_context.finalize_scenario(self.scenario.id)

        self.context_registry.register_context('configuration', config_context)
        self.contexts['configuration'] = config_context  # Backward compatibility

        # Register Railway Infrastructure Context
        railway_context = RailwayInfrastructureContext(self.scenario)
        self.context_registry.register_context('railway', railway_context)
        self.contexts['railway'] = railway_context

        # Register Shunting Operations Context
        shunting_context = ShuntingOperationsContext(self.infra.event_bus)
        self.context_registry.register_context('shunting', shunting_context)
        self.contexts['shunting'] = shunting_context

        # Register External Trains Context
        external_trains_context = ExternalTrainsContext(self.infra.event_bus)
        self.context_registry.register_context('external_trains', external_trains_context)
        self.contexts['external_trains'] = external_trains_context

        # Register Yard Operations Context
        yard_context = YardOperationsContext(self.infra)
        self.context_registry.register_context('yard', yard_context)
        self.contexts['yard'] = yard_context

        # Register PopUp Retrofit Context
        popup_context = PopUpRetrofitContext(self.infra.event_bus)
        self.context_registry.register_context('popup', popup_context)
        self.contexts['popup'] = popup_context

        # Register Analytics Context
        analytics_repository = InMemoryAnalyticsRepository()
        analytics_context = AnalyticsContext(self.infra.event_bus, analytics_repository)
        self.context_registry.register_context('analytics', analytics_context)
        self.contexts['analytics'] = analytics_context

    def _start_processes(self) -> None:
        """Start all context processes using registry."""
        logger.info(' Starting processes for all contexts')

        # Start all context processes through registry
        self.context_registry.start_all_processes()

        # Start main simulation orchestration process
        self.engine.schedule_process(self._orchestrate_simulation())

    def _setup_workshop_infrastructure(self) -> None:
        """Set workshop infrastructure from scenario configuration up."""
        # Create PopUp workshops from scenario
        popup_context = self.contexts.get('popup')
        if popup_context and self.scenario.workshops:
            for workshop_dto in self.scenario.workshops:
                popup_context.create_workshop(
                    workshop_id=workshop_dto.track,
                    location=workshop_dto.track,
                    num_bays=workshop_dto.retrofit_stations,
                )
                popup_context.start_workshop_operations(workshop_dto.track)

        # Setup wagon flow infrastructure
        if self.scenario.workshops:
            for workshop in self.scenario.workshops:
                workshop_id = workshop.track
                if workshop_id not in self.infra.wagons_for_retrofit:
                    self.infra.wagons_for_retrofit[workshop_id] = self.engine.create_store()

        # Cross-context references already set in _initialize_contexts

    def _collect_results(self, duration: float) -> SimulationResult:
        """Collect results from all contexts using registry."""
        logger.info(' Collecting results from all contexts')

        # Get metrics from all contexts through registry
        all_metrics = self.context_registry.get_all_metrics()

        # Enhanced metrics from Analytics Context if available
        analytics_context = self.contexts.get('analytics')
        if analytics_context and hasattr(analytics_context, 'compute_all_metrics'):
            enhanced_metrics = analytics_context.compute_all_metrics(self.scenario)
            all_metrics.update(enhanced_metrics)

        # Add infrastructure metrics
        all_metrics['infrastructure'] = self.infra.get_metrics()

        return SimulationResult(metrics=all_metrics, duration=duration, success=True)

    def _orchestrate_simulation(self) -> Any:
        """Orchestrate main simulation process."""
        # External Trains Context handles wagon creation and train arrivals
        # Just wait for simulation to complete
        yield from self.engine.delay(0)
