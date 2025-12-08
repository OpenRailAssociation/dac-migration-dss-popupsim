"""PopUp Workshop aggregate for temporary DAC installation facilities."""

from enum import Enum
from typing import Any

from contexts.popup_retrofit.domain.entities.retrofit_bay import RetrofitBay
from contexts.popup_retrofit.domain.events.retrofit_events import RetrofitCompletedEvent
from contexts.popup_retrofit.domain.events.retrofit_events import RetrofitStartedEvent
from contexts.popup_retrofit.domain.value_objects.popup_metrics import PopUpMetrics
from contexts.popup_retrofit.domain.value_objects.retrofit_result import RetrofitResult
from contexts.popup_retrofit.domain.value_objects.workshop_id import WorkshopId
from pydantic import BaseModel
from pydantic import Field


class WorkshopStatus(Enum):
    """Status of PopUp workshop."""

    SETUP = 'setup'
    OPERATIONAL = 'operational'
    TEARDOWN = 'teardown'


class PopUpWorkshop(BaseModel):
    """Temporary retrofit facility for DAC installation."""

    workshop_id: WorkshopId = Field(description='Unique identifier for the PopUp workshop')
    location: str = Field(description='Location of the workshop')
    status: WorkshopStatus = Field(default=WorkshopStatus.SETUP, description='Current workshop status')
    retrofit_bays: list[RetrofitBay] = Field(description='Available retrofit work positions')
    metrics: PopUpMetrics = Field(default_factory=PopUpMetrics, description='Workshop performance metrics')

    def start_operations(self) -> None:
        """Start workshop operations."""
        if self.status != WorkshopStatus.SETUP:
            msg = f'Workshop {self.workshop_id.value} is not in setup status'
            raise ValueError(msg)
        self.status = WorkshopStatus.OPERATIONAL

    def process_wagon(self, wagon_id: str, current_time: float = 0.0) -> tuple[RetrofitResult, list[Any]]:
        """Process wagon for DAC installation.

        Returns
        -------
            Tuple of (retrofit_result, domain_events)
        """
        if self.status != WorkshopStatus.OPERATIONAL:
            msg = f'Workshop {self.workshop_id.value} is not operational'
            raise ValueError(msg)

        # Find available bay
        available_bay = next((bay for bay in self.retrofit_bays if bay.is_available()), None)

        if not available_bay:
            return RetrofitResult.failed(wagon_id=wagon_id, reason='No available bay for retrofit'), []

        events: list[Any] = []

        # Fire retrofit started event
        start_event = RetrofitStartedEvent(
            wagon_id=wagon_id,
            workshop_id=self.workshop_id.value,
            bay_id=available_bay.id.value,
            event_timestamp=current_time,
        )
        events.append(start_event)

        # Assign bay
        available_bay.occupy(wagon_id)

        # Simulate retrofit (basic implementation)
        retrofit_duration = 30.0  # 30 minutes base time
        completion_time = current_time + retrofit_duration

        # Complete retrofit (always successful for now)
        result = RetrofitResult.successful(
            wagon_id=wagon_id,
            duration=retrofit_duration,
            reason='DAC installed successfully',
        )

        # Fire retrofit completed event
        complete_event = RetrofitCompletedEvent(
            wagon_id=wagon_id,
            workshop_id=self.workshop_id.value,
            bay_id=available_bay.id.value,
            event_timestamp=completion_time,
            success=True,
            duration=retrofit_duration,
        )
        events.append(complete_event)

        # Update metrics
        self.metrics.record_wagon_processed(retrofit_duration, success=True)

        # Release bay
        available_bay.release()

        return result, events

    def get_available_bay_count(self) -> int:
        """Get number of available bays."""
        return sum(1 for bay in self.retrofit_bays if bay.is_available())

    def has_available_bays(self) -> bool:
        """Check if workshop has any available bays."""
        return self.get_available_bay_count() > 0

    def get_performance_summary(self) -> dict[str, Any]:
        """Get PopUp workshop performance summary."""
        return {
            'workshop_id': self.workshop_id.value,
            'wagons_processed': self.metrics.total_wagons_processed,
            'success_rate': self.metrics.success_rate,
            'bay_utilization': self.metrics.bay_utilization_percentage,
            'wagons_per_hour': self.metrics.wagons_per_hour,
            'efficiency_score': self.metrics.calculate_efficiency_score(),
            'bottleneck_analysis': self.metrics.get_bottleneck_analysis(),
        }
