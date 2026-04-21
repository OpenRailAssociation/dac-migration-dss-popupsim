"""External Trains Context application layer.

Notes
-----
    This context might be superseeded. The general business logic might change.
    Instead of having train arrivals infomration about which wagons arrive at
    which time are provided.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from contexts.configuration.domain.models.scenario import Scenario
from contexts.external_trains.domain.aggregates.train_schedule import TrainSchedule
from contexts.external_trains.domain.entities.external_train import ExternalTrain
from contexts.external_trains.domain.value_objects.train_id import TrainId
from infrastructure.event_bus.event_bus import EventBus
from infrastructure.logging import get_process_logger
from shared.domain.entities.wagon import Wagon
from shared.domain.entities.wagon import WagonStatus
from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
from shared.domain.events.wagon_lifecycle_events import WagonRetrofitCompletedEvent
from shared.infrastructure.time_converters import datetime_to_ticks

from .ports.external_trains_context_port import ExternalTrainsContextPort

if TYPE_CHECKING:
    from shared.infrastructure.simulation.coordination.simulation_infrastructure import SimulationInfrastructure


class ExternalTrainsContext(ExternalTrainsContextPort):
    """External Trains Context managing train arrivals - Single Source of Truth for wagons."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.train_schedule = TrainSchedule()
        self.infra: SimulationInfrastructure | None = None
        self.scenario: Scenario | None = None
        self._wagons: dict[str, Any] = {}  # Single source of truth for wagon state

    def initialize(self, infra: Any) -> None:
        """Initialize with infrastructure.

        Args:
            infra: Simulation infrastructure
        """
        self.infra = infra
        # Don't reset scenario - it's set before initialization

    def start_processes(self) -> None:
        """Start train arrival processes."""
        if self.infra and self.scenario:
            # Schedule each train as a separate process to avoid generator stopping mid-execution
            for train in self.scenario.trains:
                self.infra.engine.schedule_process(self._process_single_train_arrival(train))

        # Subscribe to completion events to update wagon state
        self.event_bus.subscribe(WagonRetrofitCompletedEvent, self._handle_wagon_completed)  # type: ignore[arg-type]

    def _process_single_train_arrival(self, train: Any) -> Any:
        """Process a single train arrival."""
        # Wait for train arrival time
        arrival_time = (
            train.arrival_time
            if isinstance(train.arrival_time, datetime)
            else datetime.fromisoformat(train.arrival_time)
        )
        arrival_delay = datetime_to_ticks(arrival_time, self.scenario.start_date)  # type: ignore[attr-defined]

        if arrival_delay > 0:
            yield from self.infra.engine.delay(arrival_delay)  # type: ignore[union-attr]

        # Get arrival track from train configuration
        arrival_track = train.arrival_track or 'collection'

        current_time = self.infra.engine.current_time()  # type: ignore[union-attr]

        # Log train arrival
        try:
            plog = get_process_logger()
            plog.log(
                f'TRAIN {train.train_id}: Arrived at {arrival_track} with {len(train.wagons)} wagons',
                sim_time=current_time,
            )
        except RuntimeError:
            pass

        # Create actual wagon entities and store as single source of truth
        train_wagons: list[Wagon] = []
        for wagon_dto in train.wagons:
            wagon = Wagon(
                id=wagon_dto.id,
                length=wagon_dto.length,
                is_loaded=wagon_dto.is_loaded,
                track=arrival_track,
                needs_retrofit=wagon_dto.needs_retrofit,
                status=WagonStatus.UNKNOWN,
            )
            train_wagons.append(wagon)
            self._wagons[wagon.id] = wagon  # Store as single source of truth

            # Log individual wagon arrival
            try:
                plog = get_process_logger()
                plog.log(
                    f'  WAGON {wagon.id}: Arrived on {arrival_track} (length={wagon.length}m)',
                    sim_time=current_time,
                )
            except RuntimeError:
                pass

        # Publish train arrived event with actual wagons
        event = TrainArrivedEvent(
            train_id=train.train_id,
            wagons=train_wagons,
            arrival_track=arrival_track,
            event_timestamp=current_time,
        )
        self.event_bus.publish(event)

        # Minimal delay to allow event processing
        yield from self.infra.engine.delay(0.0)  # type: ignore[union-attr]

    def schedule_train(self, train_id: str, arrival_time: float, wagons: list[Any]) -> None:
        """Schedule external train arrival."""
        train = ExternalTrain(id=TrainId(train_id), scheduled_arrival=arrival_time, wagons=wagons)
        self.train_schedule.add_train(train)

    def process_arrivals(self, current_time: float) -> None:
        """Process scheduled train arrivals."""
        scheduled_trains = self.train_schedule.get_scheduled_trains()

        for train in scheduled_trains:
            if train.scheduled_arrival <= current_time:
                event = self.train_schedule.process_arrival(train.id, current_time)
                self.event_bus.publish(event)  # type: ignore[arg-type]

    def get_scheduled_count(self) -> int:
        """Get count of scheduled trains."""
        return len(self.train_schedule.get_scheduled_trains())

    def _handle_wagon_completed(self, event: WagonRetrofitCompletedEvent) -> None:
        """Handle wagon retrofit completion - update wagon state."""
        wagon = self._wagons.get(event.wagon_id)
        if wagon:
            wagon.status = WagonStatus.RETROFITTED
            wagon.retrofit_end_time = event.completion_time

    def get_completed_wagons(self) -> list[Wagon]:
        """Get all completed wagons for test validation."""
        return [w for w in self._wagons.values() if w.status == WagonStatus.PARKING]

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics."""
        return {
            'scheduled_trains': self.get_scheduled_count(),
            'processed_trains': 0,
            'total_wagons': len(self._wagons),
            'completed_wagons': len(self.get_completed_wagons()),
        }

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {'status': 'ready'}

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
