"""Shunting Operations Context - Active bounded context for yard shunting operations."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from analytics.application.metrics_aggregator import SimulationMetrics
from analytics.domain.collectors.locomotive_collector import LocomotiveCollector
from configuration.domain.models.scenario import Scenario
from workshop_operations.application.factories.entity_factory import EntityFactory
from workshop_operations.application.services.locomotive_service import (
    LocomotiveService,
)
from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.services.locomotive_operations import (
    LocomotiveStateManager,
)
from workshop_operations.infrastructure.resources.resource_pool import (
    ResourcePool,
    Trackable,
)

from shunting_operations.application.shunting_locomotive_service import (
    ShuntingLocomotiveService,
)
from shunting_operations.application.shunting_service import (
    DefaultShuntingService,
    ShuntingService,
)

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession

logger = logging.getLogger(__name__)


@dataclass
class _ShuntingResources:
    """Internal container for shunting resources."""

    locomotives_queue: list[Locomotive]
    locomotives_pool: ResourcePool | None = None
    metrics: SimulationMetrics | None = None


class ShuntingOperationsContext:
    """Active bounded context for yard shunting operations.

    Manages:
    - Locomotive pool and allocation
    - Shunting operations (coupling, decoupling, movement)
    - Locomotive state and metrics
    - Future: Train marshalling, automated shunting plans
    """

    def __init__(
        self, scenario: Scenario, shunting_service: ShuntingService | None = None
    ) -> None:
        """Initialize shunting operations context.

        Parameters
        ----------
        scenario : Scenario
            Simulation scenario with locomotive configuration
        shunting_service : ShuntingService | None
            Custom shunting service (default: DefaultShuntingService)
        """
        self.scenario = scenario
        self.shunting_service = shunting_service or DefaultShuntingService()
        self._locomotive_service = ShuntingLocomotiveService(self.shunting_service)
        self.loco_state = LocomotiveStateManager()

        # Convert locomotive DTOs to entities
        locomotives_collection = [
            EntityFactory.create_locomotive(dto) for dto in (scenario.locomotives or [])
        ]
        for loco in locomotives_collection:
            loco.record_status_change(0.0, loco.status)

        self._resources = _ShuntingResources(locomotives_queue=locomotives_collection)
        self.session: SimulationSession | None = None

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize context with simulation session.

        Parameters
        ----------
        simulation_session : SimulationSession
            Active simulation session
        """
        self.session = simulation_session

        # Initialize locomotive resource pool
        self._resources.locomotives_pool = ResourcePool(
            simulation_session.engine,
            cast(list[Trackable], self._resources.locomotives_queue),
            "Locomotives",
        )

        # Initialize metrics collection
        self._resources.metrics = SimulationMetrics()
        self._resources.metrics.register(LocomotiveCollector())

        logger.info(
            "✅ SHUNTING CONTEXT: Initialized with %d locomotives",
            len(self._resources.locomotives_queue),
        )

    def start_processes(self) -> None:
        """Start shunting simulation processes.

        Currently passive - triggered by workshop operations.
        Future: Active optimization, conflict resolution, scheduling.
        """
        if self.session is None:
            raise RuntimeError("Context not initialized")

        logger.info("🚂 SHUNTING CONTEXT: Ready for operations (passive mode)")
        # Future: Schedule active shunting optimization processes

    def get_metrics(self) -> dict[str, Any]:
        """Get shunting-specific metrics.

        Returns
        -------
        dict[str, Any]
            Locomotive utilization and shunting operation metrics
        """
        if self._resources.metrics is None:
            return {}

        base_metrics: dict[str, Any] = dict(self._resources.metrics.get_results())

        # Calculate locomotive utilization
        if self._resources.locomotives_pool and self.session:
            total_locos = len(self._resources.locomotives_queue)
            available = self._resources.locomotives_pool.get_available_count()
            in_use = total_locos - available
            utilization = (in_use / total_locos * 100) if total_locos > 0 else 0.0

            base_metrics["locomotive_utilization_pct"] = round(utilization, 2)
            base_metrics["locomotives_in_use"] = in_use
            base_metrics["locomotives_available"] = available
            base_metrics["locomotives_total"] = total_locos

        # Future: Add coupling_efficiency, shunting_conflicts metrics

        return base_metrics

    def cleanup(self) -> None:
        """Cleanup shunting resources."""
        logger.info("🧹 SHUNTING CONTEXT: Cleanup complete")

    def get_locomotive_service(self) -> LocomotiveService:
        """Get locomotive service for shunting operations.

        Returns
        -------
        LocomotiveService
            Service for allocating, moving, and managing locomotives
        """
        return self._locomotive_service

    def get_shunting_service(self) -> ShuntingService:
        """Get native shunting service for advanced operations.

        Returns
        -------
        ShuntingService
            Low-level shunting operations service
        """
        return self.shunting_service

    @property
    def locomotives(self) -> ResourcePool | None:
        """Get locomotives resource pool (backward compatibility)."""
        return self._resources.locomotives_pool

    @property
    def locomotives_collection(self) -> list[Locomotive]:
        """Get locomotives collection (backward compatibility)."""
        return self._resources.locomotives_queue

    @property
    def metrics(self) -> SimulationMetrics | None:
        """Get metrics aggregator (backward compatibility)."""
        return self._resources.metrics
