"""KPI Calculator - calculates performance metrics from simulation results."""

import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.domain.entities.workshop import Workshop

from configuration.domain.models.scenario import Scenario

from ..factories.analytics_factory import AnalyticsFactory
from ..models.kpi_result import BottleneckInfo
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

    def calculate_from_simulation(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        metrics: dict[str, list[dict[str, Any]]],
        scenario: Scenario,
        wagons: list[Wagon],
        rejected_wagons: list[Wagon],
        workshops: list[Workshop],
        popup_context: Any = None,  # PopUpRetrofitContext - optional for backward compatibility
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

        throughput = self._calculate_throughput(scenario, wagons, rejected_wagons)
        utilization = self._calculate_utilization(workshops, wagons)
        bottlenecks = self._identify_bottlenecks(throughput, utilization)
        avg_flow_time = self._calculate_avg_flow_time(metrics)
        avg_waiting_time = self._calculate_avg_waiting_time(wagons)

        # Collect PopUp metrics if context provided
        popup_metrics = self._collect_popup_metrics(popup_context) if popup_context else {}

        analysis_data = {
            'utilization': utilization,
            'bottlenecks': bottlenecks,
            'avg_flow_time': avg_flow_time,
            'avg_waiting_time': avg_waiting_time,
            'popup_metrics': popup_metrics,
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
        self, throughput: ThroughputKPI, utilization: list[UtilizationKPI]
    ) -> list[BottleneckInfo]:
        """Identify bottlenecks using specifications."""
        bottlenecks: list[BottleneckInfo] = []

        # Use specifications for business rules
        high_rejection_spec = HighRejectionRateSpec()
        high_utilization_spec = HighUtilizationSpec()
        critical_utilization_spec = CriticalUtilizationSpec()

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

    def _collect_popup_metrics(self, popup_context: Any) -> dict[str, Any]:
        """Collect PopUp-specific metrics from PopUp context."""
        try:
            metrics: dict[str, Any] = popup_context.get_all_workshop_metrics()
            return metrics
        except (AttributeError, TypeError, KeyError) as e:
            logger.warning('Failed to collect PopUp metrics: %s', e)
            return {}
