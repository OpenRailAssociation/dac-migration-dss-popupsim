"""Process times configuration model."""

from datetime import timedelta
import json
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from shared.infrastructure.time_converters import to_ticks


class ProcessTimes(BaseModel):
    """Process timing configuration for simulation operations."""

    train_to_hump_delay: timedelta = Field(
        default=timedelta(minutes=10.0),
        description='Time from train arrival to first wagon at hump',
    )
    wagon_hump_interval: timedelta = Field(
        default=timedelta(minutes=2.0),
        description='Time between wagons passing through hump',
    )
    screw_coupling_time: timedelta = Field(
        default=timedelta(minutes=1.0),
        description='Time for one screw coupling operation',
    )
    screw_decoupling_time: timedelta = Field(
        default=timedelta(minutes=1.0),
        description='Time for one screw decoupling operation',
    )
    dac_coupling_time: timedelta = Field(
        default=timedelta(minutes=0.5),
        description='Time for one DAC coupling operation',
    )
    dac_decoupling_time: timedelta = Field(
        default=timedelta(minutes=0.5),
        description='Time for one DAC decoupling operation',
    )
    wagon_move_to_next_station: timedelta = Field(
        default=timedelta(minutes=0.5),
        description='Time to move wagons to next station',
    )
    wagon_coupling_time: timedelta = Field(
        default=timedelta(minutes=1.0), description='Legacy: Time to couple one wagon'
    )
    wagon_decoupling_time: timedelta = Field(
        default=timedelta(minutes=1.0), description='Legacy: Time to decouple one wagon'
    )
    wagon_coupling_retrofitted_time: timedelta = Field(
        default=timedelta(minutes=2.0),
        description='Legacy: Time to couple retrofitted wagon',
    )
    wagon_retrofit_time: timedelta = Field(
        default=timedelta(minutes=60.0),
        description='Time to retrofit one wagon at a station',
    )
    loco_parking_delay: timedelta = Field(
        default=timedelta(minutes=0.0),
        description='Time locomotive waits at parking before next trip',
    )

    @field_validator('*', mode='before')
    @classmethod
    def convert_float_to_timedelta(cls, v: float | timedelta) -> timedelta:
        """Convert float minutes to timedelta for backward compatibility."""
        if isinstance(v, (int, float)):
            return timedelta(minutes=float(v))
        return v

    def get_coupling_time(self, coupler_type: str) -> timedelta:
        """Get coupling time as timedelta."""
        if coupler_type.upper() == 'DAC':
            return self.dac_coupling_time
        return self.screw_coupling_time

    def get_decoupling_time(self, coupler_type: str) -> timedelta:
        """Get decoupling time as timedelta."""
        if coupler_type.upper() == 'DAC':
            return self.dac_decoupling_time
        return self.screw_decoupling_time

    def get_coupling_ticks(self, coupler_type: str) -> float:
        """Get coupling time in SimPy ticks."""
        return to_ticks(self.get_coupling_time(coupler_type))

    def get_decoupling_ticks(self, coupler_type: str) -> float:
        """Get decoupling time in SimPy ticks."""
        return to_ticks(self.get_decoupling_time(coupler_type))

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> 'ProcessTimes':
        """Load process times from JSON file."""
        path = Path(file_path)
        if not path.exists():
            msg = f'Process times file not found: {path}'
            raise FileNotFoundError(msg)

        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(**data)
