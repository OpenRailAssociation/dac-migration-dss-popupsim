"""Specialist team entity for DAC installation technicians."""

from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class TeamStatus(Enum):
    """Status of a specialist team."""

    AVAILABLE = 'available'
    WORKING = 'working'
    BREAK = 'break'


class SpecialistTeam(BaseModel):
    """Skilled technicians for DAC installation."""

    team_id: str = Field(description='Unique identifier for the specialist team')
    team_size: int = Field(gt=0, description='Number of technicians in team')
    status: TeamStatus = Field(default=TeamStatus.AVAILABLE, description='Current status of the team')
    current_bay_id: str | None = Field(default=None, description='ID of bay team is working on')

    def assign_to_bay(self, bay_id: str) -> None:
        """Assign team to work on a specific bay."""
        if self.status != TeamStatus.AVAILABLE:
            raise ValueError(f'Team {self.team_id} is not available')
        self.status = TeamStatus.WORKING
        self.current_bay_id = bay_id

    def complete_work(self) -> None:
        """Complete work and make team available."""
        self.status = TeamStatus.AVAILABLE
        self.current_bay_id = None
