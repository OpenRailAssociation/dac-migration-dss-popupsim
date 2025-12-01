"""Analytics domain exceptions."""


class AnalyticsError(Exception):
    """Base exception for analytics domain."""


class KPICalculationError(AnalyticsError):
    """Error during KPI calculation."""


class MetricsCollectionError(AnalyticsError):
    """Error during metrics collection."""


class BottleneckAnalysisError(AnalyticsError):
    """Error during bottleneck analysis."""


class InvalidMetricsError(AnalyticsError):
    """Invalid or malformed metrics data."""
