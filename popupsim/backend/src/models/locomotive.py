"""Locomotive model for DAC retrofit operations."""

from datetime import UTC
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import field_validator


class LocoStatus(Enum):
    """Locomotive status events"""

    PARKING = 'parking'
    MOVING = 'moving'
    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'


class Locomotive(BaseModel):
    """Locomotive configuration for workshop operations."""

    locomotive_id: str
    name: str
    start_date: datetime
    end_date: datetime
    track_id: str
    status: LocoStatus = LocoStatus.PARKING
    status_history: list[tuple[float, LocoStatus]] = []

    def record_status_change(self, sim_time: float, new_status: LocoStatus) -> None:
        """Record status change with timestamp."""
        self.status_history.append((float(sim_time), new_status))
        self.status = new_status

    def get_utilization(self, total_sim_time: float) -> dict[str, float]:
        """Calculate time spent in each status as percentage."""
        sim_time = float(total_sim_time)
        if not self.status_history:
            return {status.value: 0.0 for status in LocoStatus}

        time_in_status = {status.value: 0.0 for status in LocoStatus}

        for i in range(len(self.status_history)):
            current_time, current_status = self.status_history[i]
            next_time = self.status_history[i + 1][0] if i + 1 < len(self.status_history) else sim_time
            duration = float(next_time) - float(current_time)
            time_in_status[current_status.value] += duration

        return {status: (time / sim_time * 100) if sim_time > 0 else 0.0 for status, time in time_in_status.items()}

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_datetime(cls, value: str | datetime) -> datetime:
        """Parse datetime from string."""
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
        if isinstance(value, datetime):
            return value
        msg = f'Expected str or datetime, got {type(value)}'
        raise TypeError(msg)
