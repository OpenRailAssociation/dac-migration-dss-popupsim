"""Bay ID value object."""

from pydantic import BaseModel, Field


class BayId(BaseModel):
    """Retrofit bay identifier."""

    value: str = Field(description="Bay identifier value")

    def __str__(self) -> str:
        return self.value
