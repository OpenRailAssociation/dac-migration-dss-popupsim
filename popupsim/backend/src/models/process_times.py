"""Process times configuration model."""

import json
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class ProcessTimes(BaseModel):
    """Process timing configuration for simulation operations."""

    train_to_hump_delay: float = Field(
        default=10.0, ge=0, description='Time in minutes from train arrival to first wagon at hump'
    )
    wagon_hump_interval: float = Field(
        default=2.0, ge=0, description='Time in minutes between wagons passing through hump'
    )
    wagon_coupling_time: float = Field(default=1.0, ge=0, description='Time in minutes to couple one wagon')
    wagon_decoupling_time: float = Field(default=1.0, ge=0, description='Time in minutes to decouple one wagon')
    wagon_move_to_next_station: float = Field(
        default=0.5, ge=0, description='Time in minutes to move wagons to next station'
    )
    wagon_coupling_retrofitted_time: float = Field(
        default=2.0, ge=0, description='Time in minutes to couple retrofitted wagon (DAC coupler)'
    )
    wagon_retrofit_time: float = Field(
        default=60.0, ge=0, description='Time in minutes to retrofit one wagon at a station'
    )

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> 'ProcessTimes':
        """Load process times from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Process times file not found: {path}')

        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(**data)
