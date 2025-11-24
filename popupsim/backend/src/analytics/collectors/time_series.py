"""Time-series data collector using numpy arrays."""

from dataclasses import dataclass
from dataclasses import field

import numpy as np


@dataclass
class TimeSeriesCollector:
    """Collect time-series data efficiently using numpy arrays.

    Stores timestamps and values as numpy arrays for efficient computation.
    """

    timestamps: np.ndarray = field(default_factory=lambda: np.array([]))
    values: np.ndarray = field(default_factory=lambda: np.array([]))

    def record(self, timestamp: float, value: float) -> None:
        """Record a time-series data point.

        Parameters
        ----------
        timestamp : float
            Timestamp of the measurement.
        value : float
            Measured value.
        """
        self.timestamps = np.append(self.timestamps, timestamp)
        self.values = np.append(self.values, value)

    def get_mean(self) -> float:
        """Get mean value."""
        return float(np.mean(self.values)) if len(self.values) > 0 else 0.0

    def get_std(self) -> float:
        """Get standard deviation."""
        return float(np.std(self.values)) if len(self.values) > 0 else 0.0

    def get_percentile(self, percentile: float) -> float:
        """Get percentile value.

        Parameters
        ----------
        percentile : float
            Percentile to calculate (0-100).

        Returns
        -------
        float
            Percentile value.
        """
        return float(np.percentile(self.values, percentile)) if len(self.values) > 0 else 0.0

    def get_rate_of_change(self) -> np.ndarray:  # type: ignore[no-any-return]
        """Calculate rate of change between consecutive values.

        Returns
        -------
        np.ndarray
            Rate of change array.
        """
        if len(self.values) < 2:
            return np.array([])
        return np.diff(self.values) / np.diff(self.timestamps)  # type: ignore[no-any-return]

    def resample(self, interval: float) -> tuple[np.ndarray, np.ndarray]:
        """Resample time-series to fixed intervals.

        Parameters
        ----------
        interval : float
            Resampling interval.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Resampled timestamps and values.
        """
        if len(self.timestamps) == 0:
            return np.array([]), np.array([])

        new_timestamps = np.arange(self.timestamps[0], self.timestamps[-1], interval)
        new_values = np.interp(new_timestamps, self.timestamps, self.values)
        return new_timestamps, new_values

    def reset(self) -> None:
        """Reset collector state."""
        self.timestamps = np.array([])
        self.values = np.array([])
