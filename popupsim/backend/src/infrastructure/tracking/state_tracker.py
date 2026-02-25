"""State tracker for point-in-time state changes."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WagonState(Enum):
    """Wagon states."""

    ARRIVED = 'arrived'
    CLASSIFIED = 'classified'
    QUEUED = 'queued'
    IN_WORKSHOP = 'in_workshop'
    RETROFITTED = 'retrofitted'
    PARKED = 'parked'
    REJECTED = 'rejected'


class LocomotiveState(Enum):
    """Locomotive states."""

    IDLE = 'idle'
    ASSIGNED = 'assigned'
    MOVING = 'moving'
    MAINTENANCE = 'maintenance'


@dataclass
class StateRecord:
    """State change record."""

    timestamp: float
    resource_id: str
    resource_type: str  # 'wagon' or 'locomotive'
    state: str
    location: str
    train_id: str | None = None
    batch_id: str | None = None


class StateTracker:
    """Tracks state changes for resources."""

    def __init__(self) -> None:
        self._state_records: list[StateRecord] = []

    def record_wagon_state(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # noqa: PLR0913
        self,
        timestamp: float,
        wagon_id: str,
        state: WagonState,
        location: str,
        train_id: str | None = None,
        batch_id: str | None = None,
    ) -> None:
        """Record wagon state change."""
        record = StateRecord(
            timestamp=timestamp,
            resource_id=wagon_id,
            resource_type='wagon',
            state=state.value,
            location=location,
            train_id=train_id,
            batch_id=batch_id,
        )
        self._state_records.append(record)

    def record_locomotive_state(
        self, timestamp: float, locomotive_id: str, state: LocomotiveState, location: str
    ) -> None:
        """Record locomotive state change."""
        record = StateRecord(
            timestamp=timestamp,
            resource_id=locomotive_id,
            resource_type='locomotive',
            state=state.value,
            location=location,
        )
        self._state_records.append(record)

    def export_to_csv(self, output_dir: Path) -> None:
        """Export state records to CSV files."""
        import pandas as pd  # pylint: disable=import-outside-toplevel

        if not self._state_records:
            return

        # All states
        all_data = []
        for record in self._state_records:
            all_data.append(
                {
                    'timestamp': record.timestamp,
                    'resource_id': record.resource_id,
                    'resource_type': record.resource_type,
                    'state': record.state,
                    'location': record.location,
                    'train_id': record.train_id or '',
                    'batch_id': record.batch_id or '',
                }
            )

        df = pd.DataFrame(all_data)
        df.to_csv(output_dir / 'resource_states.csv', index=False)

        # Wagon states only
        wagon_data = [d for d in all_data if d['resource_type'] == 'wagon']
        if wagon_data:
            wagon_df = pd.DataFrame(wagon_data)
            wagon_df.to_csv(output_dir / 'wagon_states.csv', index=False)

        # Locomotive states only
        loco_data = [d for d in all_data if d['resource_type'] == 'locomotive']
        if loco_data:
            loco_df = pd.DataFrame(loco_data)
            loco_df.to_csv(output_dir / 'locomotive_states.csv', index=False)


# Global instance
_STATE_TRACKER: StateTracker | None = None


def get_state_tracker() -> StateTracker:
    """Get state tracker instance."""
    global _STATE_TRACKER  # pylint: disable=global-statement
    if _STATE_TRACKER is None:
        _STATE_TRACKER = StateTracker()
    return _STATE_TRACKER
