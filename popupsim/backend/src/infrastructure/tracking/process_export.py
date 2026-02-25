"""Process tracking data export using existing CSV pattern."""

from pathlib import Path

from infrastructure.tracking.process_tracker import get_process_tracker
from infrastructure.tracking.state_tracker import get_state_tracker


def export_process_tracking_data(output_dir: Path) -> None:
    """Export both process tracking and state data using CSV pattern."""
    try:
        # Export process durations
        process_tracker = get_process_tracker()
        process_tracker.export_to_csv(output_dir)

        # Export state changes
        state_tracker = get_state_tracker()
        state_tracker.export_to_csv(output_dir)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f'Warning: Failed to export tracking data: {e}')
