"""Async analytics service for non-blocking KPI calculation."""

import asyncio
import logging
from typing import Any

from analytics.domain.exceptions import KPICalculationError
from analytics.domain.models.bottleneck_config import BottleneckConfig
from analytics.domain.models.kpi_result import KPIResult
from analytics.domain.models.simulation_data import ContextData, SimulationData
from analytics.domain.services.kpi_calculator import KPICalculator

logger = logging.getLogger(__name__)


class AsyncAnalyticsService:
    """Async analytics service for background KPI calculation."""

    def __init__(self, bottleneck_config: Any = None) -> None:
        config = (
            bottleneck_config
            if isinstance(bottleneck_config, BottleneckConfig)
            else None
        )
        self.kpi_calculator = KPICalculator(config)
        self._calculation_tasks: list[asyncio.Task] = []

    async def calculate_kpis_async(
        self, simulation_data: SimulationData, context_data: ContextData | None = None
    ) -> KPIResult:
        """Calculate KPIs asynchronously without blocking simulation."""
        logger.info(
            "Starting async KPI calculation for scenario %s",
            simulation_data.scenario.id,
        )

        try:
            contexts = context_data or ContextData()
            # Run KPI calculation asynchronously
            result = await self.kpi_calculator.calculate_from_simulation(
                simulation_data.metrics,
                simulation_data.scenario,
                simulation_data.wagons,
                simulation_data.rejected_wagons,
                simulation_data.workshops,
                contexts.popup_context,
                contexts.yard_context,
                contexts.shunting_context,
            )

            logger.info(
                "Completed async KPI calculation for scenario %s",
                simulation_data.scenario.id,
            )
            return result
        except Exception as e:
            logger.error(
                "Async KPI calculation failed for scenario %s: %s",
                simulation_data.scenario.id,
                e,
            )
            raise KPICalculationError(
                f"Async KPI calculation failed for scenario {simulation_data.scenario.id}"
            ) from e

    def start_background_calculation(
        self, simulation_data: SimulationData, context_data: ContextData | None = None
    ) -> asyncio.Task:
        """Start KPI calculation in background, return immediately."""
        task = asyncio.create_task(
            self.calculate_kpis_async(simulation_data, context_data)
        )
        self._calculation_tasks.append(task)
        return task

    async def wait_for_all_calculations(self) -> list[KPIResult]:
        """Wait for all background calculations to complete."""
        if not self._calculation_tasks:
            return []

        results = await asyncio.gather(*self._calculation_tasks, return_exceptions=True)
        self._calculation_tasks.clear()

        # Filter out exceptions and return successful results
        return [r for r in results if isinstance(r, KPIResult)]
