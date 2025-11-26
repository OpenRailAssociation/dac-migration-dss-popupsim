"""Tests for time-series collector."""

from analytics.collectors.time_series import TimeSeriesCollector
import numpy as np


def test_time_series_collector_initialization() -> None:
    """Test TimeSeriesCollector initialization."""
    collector = TimeSeriesCollector()

    assert len(collector.timestamps) == 0
    assert len(collector.values) == 0


def test_record_data_point() -> None:
    """Test recording data points."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 10.0)
    collector.record(1.0, 20.0)

    assert len(collector.timestamps) == 2
    assert len(collector.values) == 2
    assert collector.timestamps[0] == 0.0
    assert collector.values[1] == 20.0


def test_get_mean() -> None:
    """Test calculating mean."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 10.0)
    collector.record(1.0, 20.0)
    collector.record(2.0, 30.0)

    assert collector.get_mean() == 20.0


def test_get_std() -> None:
    """Test calculating standard deviation."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 10.0)
    collector.record(1.0, 20.0)
    collector.record(2.0, 30.0)

    std = collector.get_std()
    assert std > 0


def test_get_percentile() -> None:
    """Test calculating percentile."""
    collector = TimeSeriesCollector()

    for i in range(100):
        collector.record(float(i), float(i))

    assert collector.get_percentile(50) == 49.5


def test_get_rate_of_change() -> None:
    """Test calculating rate of change."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 0.0)
    collector.record(1.0, 10.0)
    collector.record(2.0, 20.0)

    rates = collector.get_rate_of_change()
    assert len(rates) == 2
    assert np.allclose(rates, [10.0, 10.0])


def test_resample() -> None:
    """Test resampling time-series."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 0.0)
    collector.record(10.0, 100.0)

    new_times, new_values = collector.resample(2.0)
    assert len(new_times) == 5
    assert new_values[0] == 0.0
    assert new_values[-1] == 80.0


def test_reset() -> None:
    """Test resetting collector."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 10.0)
    collector.reset()

    assert len(collector.timestamps) == 0
    assert len(collector.values) == 0


def test_empty_collector_stats() -> None:
    """Test statistics on empty collector."""
    collector = TimeSeriesCollector()

    assert collector.get_mean() == 0.0
    assert collector.get_std() == 0.0
    assert collector.get_percentile(50) == 0.0


def test_rate_of_change_insufficient_data() -> None:
    """Test rate of change with insufficient data."""
    collector = TimeSeriesCollector()

    collector.record(0.0, 10.0)
    rates = collector.get_rate_of_change()

    assert len(rates) == 0
