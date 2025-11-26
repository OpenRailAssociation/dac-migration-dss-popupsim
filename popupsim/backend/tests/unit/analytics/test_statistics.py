"""Tests for statistics calculator."""


from analytics.reporting.statistics import StatisticsCalculator


def test_calculate_summary_stats() -> None:
    """Test calculating summary statistics."""
    calculator = StatisticsCalculator()
    metrics = {
        'wagon': [
            {'name': 'wagons_delivered', 'value': 10, 'unit': 'wagons'},
            {'name': 'wagons_delivered', 'value': 15, 'unit': 'wagons'},
            {'name': 'wagons_delivered', 'value': 20, 'unit': 'wagons'},
        ],
    }

    stats = calculator.calculate_summary_stats(metrics)

    assert 'wagon' in stats
    assert 'value' in stats['wagon'].columns
    assert stats['wagon'].loc['mean', 'value'] == 15.0


def test_calculate_percentiles() -> None:
    """Test calculating percentiles."""
    calculator = StatisticsCalculator()
    metrics = {
        'wagon': [{'name': 'flow_time', 'value': i * 10, 'unit': 'min'} for i in range(1, 11)],
    }

    percentiles = calculator.calculate_percentiles(metrics, [0.5, 0.95])

    assert 'wagon' in percentiles
    assert 0.5 in percentiles['wagon'].index
    assert 0.95 in percentiles['wagon'].index


def test_empty_metrics() -> None:
    """Test with empty metrics."""
    calculator = StatisticsCalculator()
    metrics: dict = {}

    stats = calculator.calculate_summary_stats(metrics)

    assert stats == {}


def test_non_numeric_metrics() -> None:
    """Test with non-numeric metrics."""
    calculator = StatisticsCalculator()
    metrics = {
        'wagon': [
            {'name': 'status', 'value': 'completed', 'unit': ''},
        ],
    }

    stats = calculator.calculate_summary_stats(metrics)

    assert 'wagon' not in stats or stats['wagon'].empty


def test_default_percentiles() -> None:
    """Test default percentiles."""
    calculator = StatisticsCalculator()
    metrics = {
        'wagon': [{'name': 'value', 'value': i, 'unit': 'units'} for i in range(100)],
    }

    percentiles = calculator.calculate_percentiles(metrics)

    assert 'wagon' in percentiles
    assert len(percentiles['wagon']) == 5


def test_moving_average() -> None:
    """Test moving average calculation."""
    calculator = StatisticsCalculator()
    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    result = calculator.calculate_moving_average(data, window=3)

    assert len(result) == 3
    assert result[0] == 2.0


def test_correlation_matrix() -> None:
    """Test correlation matrix calculation."""
    calculator = StatisticsCalculator()
    metrics = {
        'wagon': [{'value1': i, 'value2': i * 2} for i in range(10)],
    }

    correlations = calculator.calculate_correlation_matrix(metrics)

    assert 'wagon' in correlations
    assert correlations['wagon'].loc['value1', 'value2'] == 1.0


def test_detect_outliers() -> None:
    """Test outlier detection."""
    calculator = StatisticsCalculator()
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0]

    outliers = calculator.detect_outliers(data, threshold=2.0)

    assert outliers[-1]
    assert not outliers[0]
