"""Tests for base metric collector classes."""

from analytics.domain.collectors.base import MetricCollector
from analytics.domain.collectors.base import MetricResult
import pytest


def test_metric_result_creation() -> None:
    """Test MetricResult dataclass creation."""
    metric = MetricResult(
        name='test_metric',
        value=42.5,
        unit='wagons',
        category='throughput',
    )

    assert metric.name == 'test_metric'
    assert metric.value == 42.5
    assert metric.unit == 'wagons'
    assert metric.category == 'throughput'


def test_metric_result_with_string_value() -> None:
    """Test MetricResult with string value."""
    metric = MetricResult(
        name='status',
        value='completed',
        unit='',
        category='system',
    )

    assert metric.value == 'completed'
    assert isinstance(metric.value, str)


def test_metric_result_with_int_value() -> None:
    """Test MetricResult with integer value."""
    metric = MetricResult(
        name='count',
        value=100,
        unit='items',
        category='inventory',
    )

    assert metric.value == 100
    assert isinstance(metric.value, int)


def test_metric_collector_is_abstract() -> None:
    """Test that MetricCollector cannot be instantiated directly."""
    with pytest.raises(TypeError):
        MetricCollector()  # type: ignore[abstract]
