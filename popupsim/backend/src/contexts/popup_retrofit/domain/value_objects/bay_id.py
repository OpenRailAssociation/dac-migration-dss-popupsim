"""Bay ID value object."""

from pydantic import BaseModel
from pydantic import Field


class BayId(BaseModel):
    """Retrofit bay identifier."""

    value: str = Field(description='Bay identifier value')

    def __str__(self) -> str:
        return self.value
