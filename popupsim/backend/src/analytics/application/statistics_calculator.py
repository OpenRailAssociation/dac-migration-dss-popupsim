"""Statistical analysis using pandas and numpy."""

from typing import Any

import numpy as np
import pandas as pd


class StatisticsCalculator:
    """Calculate statistics from time-series metrics."""

    def calculate_summary_stats(self, metrics: dict[str, list[dict[str, Any]]]) -> dict[str, pd.DataFrame]:
        """Calculate summary statistics for each metric category.

        Parameters
        ----------
        metrics : dict[str, list[dict[str, Any]]]
            Metrics grouped by category.

        Returns
        -------
        dict[str, pd.DataFrame]
            Summary statistics per category.
        """
        stats: dict[str, pd.DataFrame] = {}

        for category, metric_list in metrics.items():
            if metric_list:
                df = pd.DataFrame(metric_list)
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    stats[category] = df[numeric_cols].describe()

        return stats

    def calculate_percentiles(
        self, metrics: dict[str, list[dict[str, Any]]], percentiles: list[float] | None = None
    ) -> dict[str, pd.DataFrame]:
        """Calculate percentiles for numeric metrics.

        Parameters
        ----------
        metrics : dict[str, list[dict[str, Any]]]
            Metrics grouped by category.
        percentiles : list[float] | None
            Percentiles to calculate (default: [0.25, 0.5, 0.75, 0.95, 0.99]).

        Returns
        -------
        dict[str, pd.DataFrame]
            Percentile values per category.
        """
        if percentiles is None:
            percentiles = [0.25, 0.5, 0.75, 0.95, 0.99]

        results: dict[str, pd.DataFrame] = {}

        for category, metric_list in metrics.items():
            if metric_list:
                df = pd.DataFrame(metric_list)
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    results[category] = df[numeric_cols].quantile(percentiles)

        return results

    def calculate_moving_average(self, data: list[float], window: int = 5) -> np.ndarray:
        """Calculate moving average using numpy.

        Parameters
        ----------
        data : list[float]
            Time-series data.
        window : int
            Window size for moving average.

        Returns
        -------
        np.ndarray
            Moving average values.
        """
        return np.convolve(data, np.ones(window) / window, mode='valid')

    def calculate_correlation_matrix(self, metrics: dict[str, list[dict[str, Any]]]) -> dict[str, pd.DataFrame]:
        """Calculate correlation matrix for numeric metrics.

        Parameters
        ----------
        metrics : dict[str, list[dict[str, Any]]]
            Metrics grouped by category.

        Returns
        -------
        dict[str, pd.DataFrame]
            Correlation matrices per category.
        """
        correlations: dict[str, pd.DataFrame] = {}

        for category, metric_list in metrics.items():
            if metric_list:
                df = pd.DataFrame(metric_list)
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 1:
                    correlations[category] = df[numeric_cols].corr()

        return correlations

    def detect_outliers(self, data: list[float], threshold: float = 3.0) -> np.ndarray:  # type: ignore[no-any-return]
        """Detect outliers using z-score method.

        Parameters
        ----------
        data : list[float]
            Data to analyze.
        threshold : float
            Z-score threshold for outlier detection.

        Returns
        -------
        np.ndarray
            Boolean array indicating outliers.
        """
        arr = np.array(data)
        z_scores = np.abs((arr - np.mean(arr)) / np.std(arr))
        return z_scores > threshold  # type: ignore[no-any-return]
