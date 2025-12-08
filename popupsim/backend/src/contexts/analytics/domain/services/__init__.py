"""Analytics domain services."""

# New consolidated services
from .analytics_service import Alert, AnalyticsService, BottleneckAnalysis
from .capacity_metrics_calculator import CapacityMetricsCalculator

# Legacy services (kept for backward compatibility)
from .cross_context_analyzer import CrossContextAnalyzer, FlowAnalysis
from .event_collection_service import EventCollectionService
from .event_registry import EventRegistry
from .event_stream_calculator import EventStreamCalculator, KPIResult
from .event_subscription_service import EventSubscriptionService
from .flow_metrics_calculator import FlowMetricsCalculator
from .locomotive_metrics_calculator import LocomotiveMetricsCalculator
from .metrics_calculation_service import MetricsCalculationService
from .real_time_monitor import RealTimeMonitor
from .shunting_metrics_calculator import ShuntingMetricsCalculator
from .state_tracking_service import StateTrackingService
from .statistics_computation_service import StatisticsComputationService
from .time_calculator import TimeCalculator
from .workshop_metrics_calculator import WorkshopMetricsCalculator
from .yard_metrics_calculator import YardMetricsCalculator

__all__ = [
    "Alert",
    # New consolidated services
    "AnalyticsService",
    "BottleneckAnalysis",
    "CapacityMetricsCalculator",
    # Legacy services
    "CrossContextAnalyzer",
    "EventCollectionService",
    "EventRegistry",
    "EventStreamCalculator",
    "EventSubscriptionService",
    "FlowAnalysis",
    "FlowMetricsCalculator",
    "KPIResult",
    "LegacyEventCollectorService",
    "LocomotiveMetricsCalculator",
    "MetricsCalculationService",
    "RealTimeMonitor",
    "ShuntingMetricsCalculator",
    "StateTrackingService",
    "StatisticsComputationService",
    "TimeCalculator",
    "WorkshopMetricsCalculator",
    "YardMetricsCalculator",
]
