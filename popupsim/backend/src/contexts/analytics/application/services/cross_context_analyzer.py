"""Cross-context analysis service."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BottleneckAnalysis:
    """Analysis of system bottlenecks."""

    bottleneck_type: str
    severity: float  # 0.0 to 1.0
    affected_contexts: list[str]
    description: str


@dataclass
class FlowAnalysis:
    """Analysis of cross-context flow."""

    total_throughput: float
    context_utilization: dict[str, float]
    flow_efficiency: float
    idle_time_ratio: float


class CrossContextAnalyzer:
    """Analyzes interactions and dependencies across contexts."""

    def __init__(self, event_collector: Any, event_bus: Any | None = None) -> None:
        self.event_collector = event_collector
        self.event_bus = event_bus

    def analyze_bottlenecks(self) -> list[BottleneckAnalysis]:
        """Identify bottlenecks across contexts and publish events."""
        stats = self.event_collector.compute_statistics()
        bottlenecks = []

        # Analyze retrofit capacity bottleneck
        wagons_arrived = stats.get('wagons_arrived', 0)
        retrofits_completed = stats.get('retrofits_completed', 0)

        if wagons_arrived > 0:
            completion_rate = retrofits_completed / wagons_arrived
            if completion_rate < 0.8:  # Less than 80% completion
                severity = 1.0 - completion_rate
                bottleneck = BottleneckAnalysis(
                    bottleneck_type='retrofit_capacity',
                    severity=severity,
                    affected_contexts=['external_trains', 'popup_retrofit'],
                    description=f'Retrofit completion rate {completion_rate:.1%} indicates capacity bottleneck',
                )
                bottlenecks.append(bottleneck)

                # Publish event if event bus available
                if self.event_bus:
                    from contexts.analytics.domain.events.analytics_events import BottleneckDetectedEvent

                    event = BottleneckDetectedEvent(
                        bottleneck_type=bottleneck.bottleneck_type,
                        severity=bottleneck.severity,
                        affected_contexts=bottleneck.affected_contexts,
                        description=bottleneck.description,
                    )
                    self.event_bus.publish(event)

        return bottlenecks

    def analyze_flow(self) -> FlowAnalysis:
        """Analyze cross-context flow efficiency."""
        stats = self.event_collector.compute_statistics()

        # Calculate throughput metrics
        trains_arrived = stats.get('trains_arrived', 0)
        retrofits_completed = stats.get('retrofits_completed', 0)
        wagons_arrived = stats.get('wagons_arrived', 0)

        # Flow efficiency = completed / arrived
        flow_efficiency = retrofits_completed / wagons_arrived if wagons_arrived > 0 else 0.0

        # Context utilization (simplified)
        context_utilization = {
            'external_trains': 1.0 if trains_arrived > 0 else 0.0,
            'popup_retrofit': flow_efficiency,
        }

        return FlowAnalysis(
            total_throughput=retrofits_completed,
            context_utilization=context_utilization,
            flow_efficiency=flow_efficiency,
            idle_time_ratio=1.0 - flow_efficiency,
        )

    def get_cross_context_metrics(self) -> dict[str, Any]:
        """Get comprehensive cross-context metrics."""
        bottlenecks = self.analyze_bottlenecks()
        flow = self.analyze_flow()

        return {
            'bottlenecks': [
                {
                    'type': b.bottleneck_type,
                    'severity': b.severity,
                    'contexts': b.affected_contexts,
                    'description': b.description,
                }
                for b in bottlenecks
            ],
            'flow_analysis': {
                'throughput': flow.total_throughput,
                'efficiency': flow.flow_efficiency,
                'utilization': flow.context_utilization,
                'idle_ratio': flow.idle_time_ratio,
            },
        }
