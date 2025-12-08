"""PopUp Retrofit Context port definition."""

from abc import ABC, abstractmethod
from typing import Any

from contexts.popup_retrofit.domain.value_objects.retrofit_result import (
    RetrofitResult,
)


class PopUpContextPort(ABC):
    """Port for PopUp Retrofit Context operations."""

    @abstractmethod
    def create_workshop(self, workshop_id: str, location: str, num_bays: int) -> None:
        """Create a new PopUp workshop."""

    @abstractmethod
    def start_workshop_operations(self, workshop_id: str) -> None:
        """Start operations for a workshop."""

    @abstractmethod
    def process_wagon_retrofit(
        self, workshop_id: str, wagon_id: str, current_time: float
    ) -> RetrofitResult:
        """Process wagon retrofit at specified workshop."""

    @abstractmethod
    def get_workshop_metrics(self, workshop_id: str) -> dict[str, Any] | None:
        """Get performance metrics for a workshop."""

    @abstractmethod
    def get_all_workshop_metrics(self) -> dict[str, dict[str, Any]]:
        """Get performance metrics for all workshops."""
