"""Async analytics service for non-blocking KPI calculation."""

import asyncio
import logging
from typing import Any

from analytics.domain.services.kpi_calculator import KPICalculator
from analytics.domain.models.kpi_result import KPIResult
from configuration.domain.models.scenario import Scenario
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.workshop import Workshop

logger = logging.getLogger(__name__)


class AsyncAnalyticsService:
    """Async analytics service for background KPI calculation."""

    def __init__(self) -> None:
        self.kpi_calculator = KPICalculator()
        self._calculation_tasks: list[asyncio.Task] = []

    async def calculate_kpis_async(
        self,
        metrics: dict[str, list[dict[str, Any]]],
        scenario: Scenario,
        wagons: list[Wagon],
        rejected_wagons: list[Wagon],
        workshops: list[Workshop],
        popup_context: Any = None,
        yard_context: Any = None,
        shunting_context: Any = None,
    ) -> KPIResult:
        """Calculate KPIs asynchronously without blocking simulation."""
        logger.info('Starting async KPI calculation for scenario %s', scenario.id)
        
        # Run KPI calculation asynchronously
        result = await self.kpi_calculator.calculate_from_simulation(
            metrics,
            scenario,
            wagons,
            rejected_wagons,
            workshops,
            popup_context,
            yard_context,
            shunting_context,
        )
        
        logger.info('Completed async KPI calculation for scenario %s', scenario.id)
        return result

    def start_background_calculation(
        self,
        metrics: dict[str, list[dict[str, Any]]],
        scenario: Scenario,
        wagons: list[Wagon],
        rejected_wagons: list[Wagon],
        workshops: list[Workshop],
        popup_context: Any = None,
        yard_context: Any = None,
        shunting_context: Any = None,
    ) -> asyncio.Task:
        """Start KPI calculation in background, return immediately."""
        task = asyncio.create_task(
            self.calculate_kpis_async(
                metrics, scenario, wagons, rejected_wagons, workshops,
                popup_context, yard_context, shunting_context
            )
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