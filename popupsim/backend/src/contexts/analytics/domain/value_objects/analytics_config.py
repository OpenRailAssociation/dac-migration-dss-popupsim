"""Analytics configuration value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsConfig:
    """Configuration for Analytics Context."""

    # Event collection
    max_events: int = 10000
    window_hours: float = 24.0
    cache_ttl_seconds: float = 60.0

    # Monitoring thresholds
    completion_rate_critical: float = 0.5
    completion_rate_warning: float = 0.8
    throughput_drop_threshold: float = 0.3

    # Alert management
    max_alerts: int = 100

    # Visualization
    chart_dpi: int = 150
    chart_figsize_dashboard: tuple[int, int] = (16, 12)
    chart_figsize_kpi: tuple[int, int] = (14, 6)
    chart_figsize_flow: tuple[int, int] = (14, 6)
