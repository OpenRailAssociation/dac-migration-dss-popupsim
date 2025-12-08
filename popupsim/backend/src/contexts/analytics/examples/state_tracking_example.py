"""Example usage of state tracking in analytics context."""

from typing import Any


def example_state_tracking_usage(analytics_context: Any) -> None:
    """Demonstrate state tracking capabilities.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # Get current system state snapshot
    current_state = analytics_context.get_current_state()

    # Access wagon states

    # Access workshop states
    for _state in current_state["workshop_states"].values():
        pass

    # Access locomotive breakdown
    current_state["locomotive_action_breakdown"]

    # Access track occupancy
    for track_state in current_state["track_occupancy"].values():
        track_state["current_occupancy"]

    # Get specific wagon locations
    current_state["wagon_locations"]

    # List active retrofits
    active_retrofits = current_state["active_retrofits"]
    if active_retrofits:
        pass


def example_combined_metrics(analytics_context: Any) -> None:
    """Demonstrate combining state with event-based metrics.

    Args:
        analytics_context: AnalyticsContext instance
    """
    # Get current state
    state = analytics_context.get_current_state()

    # Get event-based metrics
    analytics_context.get_metrics()

    # Combine for comprehensive view

    sum(ws["working"] for ws in state["workshop_states"].values())
    sum(ws["occupied_bays"] for ws in state["workshop_states"].values())

    loco_breakdown = state["locomotive_action_breakdown"]
    total_locos = state["total_active_locomotives"]
    if total_locos > 0:
        (loco_breakdown.get("moving", 0) / total_locos) * 100

    for _track_id, _track_state in state["track_occupancy"].items():
        pass
