"""Workshop ID value object."""

from pydantic import BaseModel
from pydantic import Field


class WorkshopId(BaseModel):
    """PopUp workshop identifier."""

    value: str = Field(description='Workshop identifier value')

    def __str__(self) -> str:
        return self.value
