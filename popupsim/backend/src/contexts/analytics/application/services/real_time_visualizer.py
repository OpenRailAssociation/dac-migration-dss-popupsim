"""Real-time visualization service for analytics."""

from collections import deque
from collections.abc import Callable
from typing import Any


class RealTimeVisualizer:
    """Service for real-time visualization during simulation."""

    def __init__(self, update_callback: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.update_callback = update_callback
        self.metrics_buffer = deque(maxlen=100)  # Keep last 100 data points
        self.is_active = False

    def start_real_time_updates(self) -> None:
        """Start real-time visualization updates."""
        self.is_active = True

    def stop_real_time_updates(self) -> None:
        """Stop real-time visualization updates."""
        self.is_active = False

    def update_metrics(self, metrics: dict[str, Any], timestamp: float) -> None:
        """Update metrics for real-time visualization."""
        if not self.is_active:
            return

        # Add timestamp to metrics
        metrics_with_time = {'timestamp': timestamp, **metrics}
        self.metrics_buffer.append(metrics_with_time)

        # Trigger callback if provided
        if self.update_callback:
            self.update_callback(metrics_with_time)

    def get_current_buffer(self) -> list[dict[str, Any]]:
        """Get current metrics buffer for visualization."""
        return list(self.metrics_buffer)

    def clear_buffer(self) -> None:
        """Clear the metrics buffer."""
        self.metrics_buffer.clear()
