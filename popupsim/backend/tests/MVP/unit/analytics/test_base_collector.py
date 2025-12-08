"""Tests for base metric collector classes."""

import pytest

from popupsim.backend.src.MVP.analytics.domain.collectors.base import (
    MetricCollector,
    MetricResult,
)
from popupsim.backend.src.MVP.analytics.domain.value_objects.metric_value import (
    MetricValue,
)


def test_metric_result_creation() -> None:
    """Test MetricResult dataclass creation."""
    metric_value = MetricValue(value=42.5, unit="wagons")
    metric = MetricResult(
        name="test_metric",
        value=metric_value,
        category="throughput",
    )

    assert metric.name == "test_metric"
    assert metric.value.value == 42.5
    assert metric.value.unit == "wagons"
    assert metric.category == "throughput"


def test_metric_result_with_string_value() -> None:
    """Test MetricResult with string value."""
    metric_value = MetricValue(value="completed", unit="none")
    metric = MetricResult(
        name="status",
        value=metric_value,
        category="system",
    )

    assert metric.value.value == "completed"
    assert isinstance(metric.value.value, str)


def test_metric_result_with_int_value() -> None:
    """Test MetricResult with integer value."""
    metric_value = MetricValue(value=100, unit="items")
    metric = MetricResult(
        name="count",
        value=metric_value,
        category="inventory",
    )

    assert metric.value.value == 100
    assert isinstance(metric.value.value, int)


def test_metric_collector_is_abstract() -> None:
    """Test that MetricCollector cannot be instantiated directly."""
    with pytest.raises(TypeError):
        MetricCollector()  # type: ignore[abstract]
