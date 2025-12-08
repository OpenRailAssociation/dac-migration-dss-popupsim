"""Example usage of time-series functionality."""

from typing import Any


def example_time_series_usage(analytics_context: Any) -> None:
    """Demonstrate time-series capabilities.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # Get train arrivals over time (hourly intervals)
    train_series = analytics_context.get_time_series(
        "train_arrivals", interval_seconds=3600.0
    )

    for _timestamp, _data in train_series:
        pass

    # Get retrofits completed over time
    retrofit_series = analytics_context.get_time_series(
        "retrofits_completed", interval_seconds=3600.0
    )

    for _timestamp, _count in retrofit_series:
        pass

    # Get locomotive utilization over time
    loco_series = analytics_context.get_time_series(
        "locomotive_utilization", interval_seconds=3600.0
    )

    for _timestamp, _breakdown in loco_series:
        pass

    # Get all time-series at once
    all_series = analytics_context.get_all_time_series(
        interval_seconds=1800.0
    )  # 30-minute intervals

    for _metric_name, _series in all_series.items():
        pass


def example_visualization_data(analytics_context: Any) -> None:
    """Prepare time-series data for visualization.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # Get hourly data for charts
    train_series = analytics_context.get_time_series(
        "train_arrivals", interval_seconds=3600.0
    )

    # Extract data for plotting
    [ts for ts, _ in train_series]
    [data["count"] for _, data in train_series]
    [data["wagons"] for _, data in train_series]

    # Example: matplotlib plotting (pseudo-code)
    # plt.plot(timestamps, train_counts, label='Trains')
    # plt.plot(timestamps, wagon_counts, label='Wagons')
    # plt.xlabel('Time (hours)')
    # plt.ylabel('Count')
    # plt.legend()
    # plt.show()


def example_custom_intervals(analytics_context: Any) -> None:
    """Demonstrate different time intervals.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # 15-minute intervals for detailed analysis
    analytics_context.get_time_series("retrofits_completed", interval_seconds=900.0)

    # 1-hour intervals for overview
    analytics_context.get_time_series("retrofits_completed", interval_seconds=3600.0)

    # 4-hour intervals for high-level trends
    analytics_context.get_time_series("retrofits_completed", interval_seconds=14400.0)


def example_track_occupancy_over_time(analytics_context: Any) -> None:
    """Track occupancy changes over time.

    Args:
        analytics_context: AnalyticsContext instance
    """
    track_series = analytics_context.get_time_series(
        "track_occupancy", interval_seconds=3600.0
    )

    for timestamp, occupancy in track_series:
        timestamp / 3600
        for _track_id, _count in occupancy.items():
            pass


def example_combined_analysis(analytics_context: Any) -> None:
    """Combine time-series with current state.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # Get historical time-series
    retrofit_series = analytics_context.get_time_series(
        "retrofits_completed", interval_seconds=3600.0
    )

    # Get current state
    analytics_context.get_current_state()

    # Calculate trends
    if len(retrofit_series) >= 2:
        last_hour = retrofit_series[-1][1]
        prev_hour = retrofit_series[-2][1]
        last_hour - prev_hour
