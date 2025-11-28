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
    # Screw coupler times (before retrofit)
    screw_coupling_time: float = Field(
        default=1.0, ge=0, description='Time in minutes for one screw coupling operation'
    )
    screw_decoupling_time: float = Field(
        default=1.0, ge=0, description='Time in minutes for one screw decoupling operation'
    )

    # DAC coupler times (after retrofit)
    dac_coupling_time: float = Field(default=0.5, ge=0, description='Time in minutes for one DAC coupling operation')
    dac_decoupling_time: float = Field(
        default=0.5, ge=0, description='Time in minutes for one DAC decoupling operation'
    )

    wagon_move_to_next_station: float = Field(
        default=0.5, ge=0, description='Time in minutes to move wagons to next station'
    )

    # Legacy fields for backward compatibility
    wagon_coupling_time: float = Field(default=1.0, ge=0, description='Legacy: Time in minutes to couple one wagon')
    wagon_decoupling_time: float = Field(default=1.0, ge=0, description='Legacy: Time in minutes to decouple one wagon')
    wagon_coupling_retrofitted_time: float = Field(
        default=2.0, ge=0, description='Legacy: Time in minutes to couple retrofitted wagon'
    )
    wagon_retrofit_time: float = Field(
        default=60.0, ge=0, description='Time in minutes to retrofit one wagon at a station'
    )
    loco_parking_delay: float = Field(
        default=0.0, ge=0, description='Time in minutes locomotive waits at parking before next trip'
    )

    def get_coupling_time(self, coupler_type: str) -> float:
        """Get time for one coupling operation based on coupler type.

        Parameters
        ----------
        coupler_type : str
            'SCREW' or 'DAC'

        Returns
        -------
        float
            Time in minutes for one coupling operation
        """
        if coupler_type.upper() == 'DAC':
            return self.dac_coupling_time
        return self.screw_coupling_time

    def get_decoupling_time(self, coupler_type: str) -> float:
        """Get time for one decoupling operation based on coupler type.

        Parameters
        ----------
        coupler_type : str
            'SCREW' or 'DAC'

        Returns
        -------
        float
            Time in minutes for one decoupling operation
        """
        if coupler_type.upper() == 'DAC':
            return self.dac_decoupling_time
        return self.screw_decoupling_time

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> 'ProcessTimes':
        """Load process times from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Process times file not found: {path}')

        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(**data)
