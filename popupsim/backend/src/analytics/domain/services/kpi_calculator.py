"""KPI Calculator - calculates performance metrics from simulation results."""

import asyncio
import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.domain.entities.workshop import Workshop

from configuration.domain.models.scenario import Scenario

from ..exceptions import KPICalculationError
from ..exceptions import MetricsCollectionError
from ..factories.analytics_factory import AnalyticsFactory
from ..models.bottleneck_config import BottleneckConfig
from ..models.kpi_result import BottleneckInfo
from ..models.kpi_result import ContextMetrics
from ..models.kpi_result import KPIResult
from ..models.kpi_result import ThroughputKPI
from ..models.kpi_result import UtilizationKPI
from ..specifications.bottleneck_specifications import CriticalUtilizationSpec
from ..specifications.bottleneck_specifications import HighRejectionRateSpec
from ..specifications.bottleneck_specifications import HighUtilizationSpec

logger = logging.getLogger(__name__)


class KPICalculator:  # pylint: disable=too-few-public-methods
    """Calculate KPIs from simulation results.

    Analyzes simulation data to compute throughput, utilization,
    bottlenecks, and other performance metrics.
    """

    def __init__(self, bottleneck_config: BottleneckConfig | None = None) -> None:
        self.bottleneck_config = bottleneck_config or BottleneckConfig()

    async def calculate_from_simulation(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
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
        """Calculate all KPIs from simulation results.

        Parameters
        ----------
        metrics : dict[str, list[dict[str, Any]]]
            Raw metrics from simulation collectors.
        scenario : Scenario
            Scenario configuration.
        wagons : list[Wagon]
            Processed wagons.
        rejected_wagons : list[Wagon]
            Rejected wagons.
        workshops : list[Workshop]
            Workshop configurations.

        Returns
        -------
        KPIResult
            Complete KPI analysis.
        """
        logger.info('Calculating KPIs for scenario %s', scenario.id)

        try:
            throughput = self._calculate_throughput(scenario, wagons, rejected_wagons)
            utilization = self._calculate_utilization(workshops, wagons)
            bottlenecks = self._identify_bottlenecks(throughput, utilization, scenario.id)
            avg_flow_time = self._calculate_avg_flow_time(metrics)
            avg_waiting_time = self._calculate_avg_waiting_time(wagons)

            # Collect context-specific metrics asynchronously
            context_metrics = await self._collect_all_context_metrics_async(
                popup_context, yard_context, shunting_context
            )
        except Exception as e:
            raise KPICalculationError(f'Failed to calculate KPIs for scenario {scenario.id}: {e}') from e

        analysis_data = {
            'utilization': utilization,
            'bottlenecks': bottlenecks,
            'avg_flow_time': avg_flow_time,
            'avg_waiting_time': avg_waiting_time,
            'context_metrics': context_metrics,
        }
        return AnalyticsFactory.create_kpi_result(
            scenario_id=scenario.id,
            throughput=throughput,
            analysis_data=analysis_data,
        )

    def _calculate_throughput(
        self,
        scenario: Scenario,
        wagons: list[Wagon],
        rejected_wagons: list[Wagon],
    ) -> ThroughputKPI:
        """Calculate throughput metrics."""
        duration_hours = (scenario.end_date - scenario.start_date).total_seconds() / 3600.0

        retrofitted = sum(1 for w in wagons if w.status == WagonStatus.RETROFITTED)
        total_processed = len(wagons)
        total_rejected = len(rejected_wagons)

        return AnalyticsFactory.create_throughput_kpi(
            total_processed=total_processed,
            total_retrofitted=retrofitted,
            total_rejected=total_rejected,
            duration_hours=duration_hours,
        )

    def _calculate_utilization(self, workshops: list[Workshop], wagons: list[Wagon]) -> list[UtilizationKPI]:
        """Calculate workshop utilization metrics."""
        utilization_list: list[UtilizationKPI] = []

        for workshop in workshops:
            # Count wagons processed at this workshop
            workshop_wagons = [w for w in wagons if w.track == workshop.track]
            processed_count = len(workshop_wagons)

            utilization_list.append(AnalyticsFactory.create_utilization_kpi(workshop, processed_count))

        return utilization_list

    def _identify_bottlenecks(
        self, throughput: ThroughputKPI, utilization: list[UtilizationKPI], scenario_id: str
    ) -> list[BottleneckInfo]:
        """Identify bottlenecks using specifications."""
        bottlenecks: list[BottleneckInfo] = []

        # Create scenario-specific configuration
        config = BottleneckConfig.create_for_scenario(scenario_id)

        # Use specifications for business rules
        high_rejection_spec = HighRejectionRateSpec(config)
        high_utilization_spec = HighUtilizationSpec(config)
        critical_utilization_spec = CriticalUtilizationSpec(config)

        # Check for high rejection rate
        if high_rejection_spec.is_satisfied_by(throughput):
            rejection_rate = throughput.total_wagons_rejected / throughput.total_wagons_processed
            bottlenecks.append(
                AnalyticsFactory.create_bottleneck_info(
                    location='Collection Tracks',
                    bottleneck_type='track',
                    severity='high' if rejection_rate > 0.2 else 'medium',
                    description=f'High rejection rate: {rejection_rate * 100:.1f}% of wagons rejected',
                    impact_wagons_per_hour=throughput.wagons_per_hour * rejection_rate,
                )
            )

        # Check for high utilization workshops
        for util in utilization:
            if high_utilization_spec.is_satisfied_by(util):
                severity = 'critical' if critical_utilization_spec.is_satisfied_by(util) else 'high'
                bottlenecks.append(
                    AnalyticsFactory.create_bottleneck_info(
                        location=util.id,
                        bottleneck_type='workshop',
                        severity=severity,
                        description=f'Workshop at {util.average_utilization_percent:.1f}% utilization',
                        impact_wagons_per_hour=throughput.wagons_per_hour * 0.1,
                    )
                )

        return bottlenecks

    def _calculate_avg_flow_time(self, metrics: dict[str, list[dict[str, Any]]]) -> float:
        """Calculate average flow time from metrics."""
        wagon = metrics.get('wagon', [])
        for metric in wagon:
            if metric['name'] == 'avg_flow_time':
                return float(metric['value'])
        return 0.0

    def _calculate_avg_waiting_time(self, wagons: list[Wagon]) -> float:
        """Calculate average waiting time for wagons."""
        waiting_times = [w.waiting_time for w in wagons if w.waiting_time is not None]
        if not waiting_times:
            return 0.0
        return round(sum(waiting_times) / len(waiting_times) / 60.0, 1)  # Convert to minutes

    async def _collect_popup_metrics_async(self, popup_context: Any) -> dict[str, Any]:
        """Collect PopUp-specific metrics asynchronously."""
        try:
            if hasattr(popup_context, 'get_all_workshop_metrics_async'):
                metrics: dict[str, Any] = await popup_context.get_all_workshop_metrics_async()
            else:
                metrics = popup_context.get_all_workshop_metrics()
            return metrics
        except (AttributeError, TypeError, KeyError) as e:
            raise MetricsCollectionError(f'Failed to collect PopUp metrics: {e}') from e

    async def _collect_yard_metrics_async(self, yard_context: Any) -> dict[str, Any]:
        """Collect Yard-specific metrics asynchronously."""
        try:
            if hasattr(yard_context, 'get_yard_metrics_async'):
                metrics: dict[str, Any] = await yard_context.get_yard_metrics_async()
            else:
                metrics = yard_context.get_yard_metrics()
            return metrics
        except (AttributeError, TypeError, KeyError) as e:
            raise MetricsCollectionError(f'Failed to collect Yard metrics: {e}') from e

    def _collect_shunting_metrics(self, shunting_context: Any) -> dict[str, Any]:
        """Collect Shunting-specific metrics from Shunting context."""
        try:
            metrics: dict[str, Any] = shunting_context.get_shunting_metrics()
            return metrics
        except (AttributeError, TypeError, KeyError) as e:
            raise MetricsCollectionError(f'Failed to collect Shunting metrics: {e}') from e

    async def _collect_all_context_metrics_async(
        self, popup_context: Any, yard_context: Any, shunting_context: Any
    ) -> ContextMetrics:
        """Collect all context metrics asynchronously."""
        # Collect all metrics in parallel
        popup_task = self._collect_popup_metrics_async(popup_context) if popup_context else None
        yard_task = self._collect_yard_metrics_async(yard_context) if yard_context else None
        shunting_task = self._collect_shunting_metrics_async(shunting_context) if shunting_context else None

        # Wait for all tasks to complete
        tasks = [task for task in [popup_task, yard_task, shunting_task] if task is not None]
        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                popup_metrics = results[0] if popup_task else {}
                yard_metrics = results[1] if yard_task else {}
                shunting_metrics = results[2] if shunting_task else {}
            except Exception as e:
                raise MetricsCollectionError(f'Failed to collect context metrics: {e}') from e
        else:
            popup_metrics, yard_metrics, shunting_metrics = {}, {}, {}

        return ContextMetrics(
            popup_metrics=popup_metrics if isinstance(popup_metrics, dict) else {},
            yard_metrics=yard_metrics if isinstance(yard_metrics, dict) else {},
            shunting_metrics=shunting_metrics if isinstance(shunting_metrics, dict) else {},
        )

    def _collect_popup_metrics(self, popup_context: Any) -> dict[str, Any]:
        """Collect PopUp-specific metrics synchronously."""
        try:
            return popup_context.get_all_workshop_metrics()
        except (AttributeError, TypeError, KeyError) as e:
            logger.warning('Failed to collect PopUp metrics: %s', e)
            return {}

    def _collect_yard_metrics(self, yard_context: Any) -> dict[str, Any]:
        """Collect Yard-specific metrics synchronously."""
        try:
            return yard_context.get_yard_metrics()
        except (AttributeError, TypeError, KeyError) as e:
            logger.warning('Failed to collect Yard metrics: %s', e)
            return {}

    async def _collect_shunting_metrics_async(self, shunting_context: Any) -> dict[str, Any]:
        """Collect Shunting-specific metrics asynchronously."""
        try:
            if hasattr(shunting_context, 'get_shunting_metrics_async'):
                metrics: dict[str, Any] = await shunting_context.get_shunting_metrics_async()
            else:
                metrics = shunting_context.get_shunting_metrics()
            return metrics
        except (AttributeError, TypeError, KeyError) as e:
            raise MetricsCollectionError(f'Failed to collect Shunting metrics: {e}') from e
