"""PopUp Workshop aggregate for temporary DAC installation facilities."""

from enum import Enum
from typing import Any

from analytics.domain.events import RetrofitCompletedEvent, RetrofitStartedEvent
from analytics.domain.value_objects.timestamp import Timestamp
from pydantic import BaseModel, Field
from workshop_operations.domain.entities.wagon import CouplerType, Wagon, WagonStatus

from ..entities.retrofit_bay import RetrofitBay
from ..value_objects.popup_metrics import PopUpMetrics


class WorkshopStatus(Enum):
    """Status of PopUp workshop."""

    SETUP = "setup"
    OPERATIONAL = "operational"
    TEARDOWN = "teardown"


class RetrofitResult(BaseModel):
    """Result of DAC retrofit operation."""

    success: bool = Field(description="Whether retrofit was successful")
    duration: float = Field(description="Time taken for retrofit in minutes")
    reason: str = Field(description="Reason for success or failure")
    wagon_id: str | None = Field(default=None, description="ID of retrofitted wagon")


class PopUpWorkshop(BaseModel):
    """Temporary retrofit facility for DAC installation."""

    workshop_id: str = Field(description="Unique identifier for the PopUp workshop")
    location: str = Field(description="Location of the workshop")
    status: WorkshopStatus = Field(
        default=WorkshopStatus.SETUP, description="Current workshop status"
    )
    retrofit_bays: list[RetrofitBay] = Field(
        description="Available retrofit work positions"
    )
    metrics: PopUpMetrics = Field(
        default_factory=lambda: PopUpMetrics(workshop_id=""),
        description="Workshop performance metrics",
    )
    event_callback: Any = Field(
        default=None, exclude=True, repr=False, description="Callback for firing events"
    )

    def model_post_init(self, __context: Any) -> None:  # pylint: disable=arguments-differ
        """Initialize metrics with workshop ID."""
        if self.metrics.workshop_id == "":
            self.metrics.workshop_id = self.workshop_id

    def start_operations(self) -> None:
        """Start workshop operations."""
        if self.status != WorkshopStatus.SETUP:
            raise ValueError(f"Workshop {self.workshop_id} is not in setup status")
        self.status = WorkshopStatus.OPERATIONAL

    def process_wagon(self, wagon: Wagon, current_time: float = 0.0) -> RetrofitResult:
        """Process wagon for DAC installation."""
        if self.status != WorkshopStatus.OPERATIONAL:
            raise ValueError(f"Workshop {self.workshop_id} is not operational")

        # Find available bay
        available_bay = next(
            (bay for bay in self.retrofit_bays if bay.status.value == "available"), None
        )

        if not available_bay:
            raise ValueError("No available bay for retrofit")

        # Fire retrofit started event
        start_event = RetrofitStartedEvent.create(
            timestamp=Timestamp.from_simulation_time(current_time),
            wagon_id=wagon.id,
            workshop_id=self.workshop_id,
            station_id=available_bay.bay_id,
        )
        self._fire_event(start_event)

        # Assign bay
        available_bay.occupy(wagon.id)

        # Update wagon status
        wagon.status = WagonStatus.RETROFITTING

        # Simulate retrofit (basic implementation)
        retrofit_duration = 30.0  # 30 minutes base time
        completion_time = current_time + retrofit_duration

        # Complete retrofit (always successful for now)
        wagon.coupler_type = CouplerType.DAC
        wagon.status = WagonStatus.RETROFITTED

        # Fire retrofit completed event
        complete_event = RetrofitCompletedEvent.create(
            timestamp=Timestamp.from_simulation_time(completion_time),
            wagon_id=wagon.id,
            workshop_id=self.workshop_id,
            station_id=available_bay.bay_id,
            success=True,
        )
        self._fire_event(complete_event)

        # Update metrics
        self.metrics.total_wagons_processed += 1
        self.metrics.total_processing_time += retrofit_duration

        # Release bay
        available_bay.release()

        return RetrofitResult(
            wagon_id=wagon.id,
            success=True,
            duration=retrofit_duration,
            reason="DAC installed successfully",
        )

    def update_bay_utilization(self, occupied_hours: float, total_hours: float) -> None:
        """Update bay utilization metrics."""
        self.metrics.occupied_bay_hours += occupied_hours
        self.metrics.total_bay_hours += total_hours

    def set_event_callback(self, callback: Any) -> None:
        """Set callback for firing events."""
        self.event_callback = callback

    def _fire_event(self, event: Any) -> None:
        """Fire event if callback is set."""
        if self.event_callback:
            self.event_callback(event)

    def get_performance_summary(self) -> dict[str, float | str]:
        """Get PopUp workshop performance summary."""
        return {
            "workshop_id": self.workshop_id,
            "wagons_processed": self.metrics.total_wagons_processed,
            "success_rate": self.metrics.dac_installation_success_rate,
            "bay_utilization": self.metrics.bay_utilization_percentage,
            "wagons_per_hour": self.metrics.wagons_per_hour,
            "efficiency_score": self.metrics.calculate_efficiency_score(),
            "bottleneck_analysis": self.metrics.get_bottleneck_analysis(),
        }
