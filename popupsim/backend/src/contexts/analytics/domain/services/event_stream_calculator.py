"""Event stream calculator for performance indicators."""

from dataclasses import dataclass
from typing import Any


@dataclass
class KPIResult:
    """KPI calculation result."""

    name: str
    value: float
    unit: str
    status: str  # 'excellent', 'good', 'warning', 'critical'
    benchmark: float | None = None


class EventStreamCalculator:
    """Calculates KPIs from event stream data."""

    def __init__(self, event_collector: Any) -> None:
        self.event_collector = event_collector
        self.benchmarks = {
            'overall_equipment_effectiveness': 0.85,
            'cycle_time_efficiency': 0.90,
            'resource_utilization': 0.80,
            'quality_rate': 0.95,
        }

    def calculate_overall_equipment_effectiveness(self) -> KPIResult:
        """Calculate OEE = Availability * Performance × Quality."""
        stats = self.event_collector.compute_statistics()

        availability = 0.95  # Assume 95% availability

        # Performance = actual throughput / theoretical throughput
        actual_throughput = stats.get('retrofits_completed', 0)
        theoretical_throughput = stats.get('wagons_arrived', 1)  # Avoid division by zero
        performance = min(actual_throughput / theoretical_throughput, 1.0)

        # Quality (assume 100% for now)
        quality = 1.0

        oee = availability * performance * quality
        status = self._get_status(oee, self.benchmarks['overall_equipment_effectiveness'])

        return KPIResult(
            name='Overall Equipment Effectiveness',
            value=oee,
            unit='%',
            status=status,
            benchmark=self.benchmarks['overall_equipment_effectiveness'],
        )

    def calculate_cycle_time_efficiency(self) -> KPIResult:
        """Calculate cycle time efficiency."""
        stats = self.event_collector.compute_statistics()

        # Simplified calculation based on completion rate
        completion_rate = stats.get('completion_rate', 0.0)

        # Cycle time efficiency inversely related to idle time
        cycle_efficiency = completion_rate * 0.95  # Assume some overhead
        status = self._get_status(cycle_efficiency, self.benchmarks['cycle_time_efficiency'])

        return KPIResult(
            name='Cycle Time Efficiency',
            value=cycle_efficiency,
            unit='%',
            status=status,
            benchmark=self.benchmarks['cycle_time_efficiency'],
        )

    def calculate_resource_utilization(self) -> KPIResult:
        """Calculate overall resource utilization."""
        stats = self.event_collector.compute_statistics()

        # Calculate based on active events vs total capacity
        total_events = stats.get('total_events', 0)
        event_types = len(stats.get('event_counts', {}))

        # Simplified utilization metric
        utilization = min(total_events / max(event_types * 10, 1), 1.0) if event_types > 0 else 0.0
        status = self._get_status(utilization, self.benchmarks['resource_utilization'])

        return KPIResult(
            name='Resource Utilization',
            value=utilization,
            unit='%',
            status=status,
            benchmark=self.benchmarks['resource_utilization'],
        )

    def calculate_throughput_variance(self) -> KPIResult:
        """Calculate throughput variance (lower is better)."""
        stats = self.event_collector.compute_statistics()

        # Simplified variance calculation
        completed = stats.get('retrofits_completed', 0)
        arrived = stats.get('wagons_arrived', 1)

        # Variance from expected throughput
        expected_rate = 0.85
        actual_rate = completed / arrived
        variance = abs(actual_rate - expected_rate) / expected_rate

        # Invert for status (lower variance is better)
        status = self._get_variance_status(variance)

        return KPIResult(
            name='Throughput Variance',
            value=variance,
            unit='ratio',
            status=status,
            benchmark=0.1,  # 10% variance benchmark
        )

    def calculate_all_kpis(self) -> list[KPIResult]:
        """Calculate all advanced KPIs."""
        return [
            self.calculate_overall_equipment_effectiveness(),
            self.calculate_cycle_time_efficiency(),
            self.calculate_resource_utilization(),
            self.calculate_throughput_variance(),
        ]

    def get_kpi_summary(self) -> dict[str, Any]:
        """Get KPI summary with status distribution."""
        kpis = self.calculate_all_kpis()

        status_counts = {'excellent': 0, 'good': 0, 'warning': 0, 'critical': 0}
        for kpi in kpis:
            status_counts[kpi.status] += 1

        return {
            'kpis': [
                {
                    'name': kpi.name,
                    'value': round(kpi.value, 3),
                    'unit': kpi.unit,
                    'status': kpi.status,
                    'benchmark': kpi.benchmark,
                }
                for kpi in kpis
            ],
            'status_distribution': status_counts,
            'overall_score': self._calculate_overall_score(kpis),
        }

    def _get_status(self, value: float, benchmark: float) -> str:
        """Get status based on value vs benchmark."""
        ratio = value / benchmark
        if ratio >= 1.0:
            return 'excellent'
        if ratio >= 0.9:
            return 'good'
        if ratio >= 0.7:
            return 'warning'
        return 'critical'

    def _get_variance_status(self, variance: float) -> str:
        """Get status for variance (lower is better)."""
        if variance <= 0.05:
            return 'excellent'
        if variance <= 0.1:
            return 'good'
        if variance <= 0.2:
            return 'warning'
        return 'critical'

    def _calculate_overall_score(self, kpis: list[KPIResult]) -> float:
        """Calculate overall performance score."""
        if not kpis:
            return 0.0

        status_weights = {
            'excellent': 1.0,
            'good': 0.8,
            'warning': 0.6,
            'critical': 0.3,
        }
        total_weight = sum(status_weights[kpi.status] for kpi in kpis)
        return total_weight / len(kpis)
