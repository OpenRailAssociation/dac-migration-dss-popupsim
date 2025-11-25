"""KPI Calculator - calculates performance metrics from simulation results."""

import logging
from typing import Any

from configuration.domain.models.scenario import Scenario
from configuration.domain.models.wagon import Wagon
from configuration.domain.models.wagon import WagonStatus
from configuration.domain.models.workshop import Workshop

from ..models.kpi_result import BottleneckInfo
from ..models.kpi_result import KPIResult
from ..models.kpi_result import ThroughputKPI
from ..models.kpi_result import UtilizationKPI

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
        logger.info('Calculating KPIs for scenario %s', scenario.scenario_id)

        throughput = self._calculate_throughput(scenario, wagons, rejected_wagons)
        utilization = self._calculate_utilization(workshops, wagons)
        bottlenecks = self._identify_bottlenecks(throughput, utilization)
        avg_flow_time = self._calculate_avg_flow_time(metrics)
        avg_waiting_time = self._calculate_avg_waiting_time(wagons)

        return KPIResult(
            scenario_id=scenario.scenario_id,
            throughput=throughput,
            utilization=utilization,
            bottlenecks=bottlenecks,
            avg_flow_time_minutes=avg_flow_time,
            avg_waiting_time_minutes=avg_waiting_time,
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

        wagons_per_hour = retrofitted / duration_hours if duration_hours > 0 else 0.0
        wagons_per_day = wagons_per_hour * 24.0

        return ThroughputKPI(
            total_wagons_processed=total_processed,
            total_wagons_retrofitted=retrofitted,
            total_wagons_rejected=total_rejected,
            simulation_duration_hours=duration_hours,
            wagons_per_hour=round(wagons_per_hour, 2),
            wagons_per_day=round(wagons_per_day, 2),
        )

    def _calculate_utilization(self, workshops: list[Workshop], wagons: list[Wagon]) -> list[UtilizationKPI]:
        """Calculate workshop utilization metrics."""
        utilization_list: list[UtilizationKPI] = []

        for workshop in workshops:
            # Calculate based on retrofit stations
            total_capacity = workshop.retrofit_stations

            # Count wagons processed at this workshop
            workshop_wagons = [w for w in wagons if w.track_id == workshop.track_id]
            processed_count = len(workshop_wagons)

            # Simple utilization estimate
            avg_utilization = min(100.0, (processed_count / total_capacity * 10) if total_capacity > 0 else 0.0)

            utilization_list.append(
                UtilizationKPI(
                    workshop_id=workshop.workshop_id,
                    total_capacity=total_capacity,
                    average_utilization_percent=round(avg_utilization, 1),
                    peak_utilization_percent=round(min(100.0, avg_utilization * 1.2), 1),
                    idle_time_percent=round(100.0 - avg_utilization, 1),
                )
            )

        return utilization_list

    def _identify_bottlenecks(
        self, throughput: ThroughputKPI, utilization: list[UtilizationKPI]
    ) -> list[BottleneckInfo]:
        """Identify bottlenecks in the system."""
        bottlenecks: list[BottleneckInfo] = []

        # Check for high rejection rate
        if throughput.total_wagons_processed > 0:
            rejection_rate = throughput.total_wagons_rejected / throughput.total_wagons_processed
            if rejection_rate > 0.1:  # More than 10% rejected
                bottlenecks.append(
                    BottleneckInfo(
                        location='Collection Tracks',
                        type='track',
                        severity='high' if rejection_rate > 0.2 else 'medium',
                        description=f'High rejection rate: {rejection_rate * 100:.1f}% of wagons rejected',
                        impact_wagons_per_hour=throughput.wagons_per_hour * rejection_rate,
                    )
                )

        # Check for high utilization workshops
        for util in utilization:
            if util.average_utilization_percent > 90:
                bottlenecks.append(
                    BottleneckInfo(
                        location=util.workshop_id,
                        type='workshop',
                        severity='critical' if util.average_utilization_percent > 95 else 'high',
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
