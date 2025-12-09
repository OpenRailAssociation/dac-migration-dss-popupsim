"""PopUp Retrofit Context implementation."""

from datetime import timedelta
from typing import Any

from contexts.popup_retrofit.domain.aggregates.popup_workshop import (
    PopUpWorkshop,
)
from contexts.popup_retrofit.domain.entities.retrofit_bay import (
    RetrofitBay,
)
from contexts.popup_retrofit.domain.services.workshop_processing_service import (
    ProcessingStrategy,
    WorkshopProcessingService,
)
from contexts.popup_retrofit.domain.value_objects.bay_id import (
    BayId,
)
from contexts.popup_retrofit.domain.value_objects.retrofit_result import (
    RetrofitResult,
)
from contexts.popup_retrofit.domain.value_objects.workshop_id import (
    WorkshopId,
)
from infrastructure.event_bus.event_bus import EventBus
from shared.domain.events.rake_events import (
    RakeProcessingStartedEvent,
    RakeTransportedEvent,
    RakeTransportRequestedEvent,
)
from shared.domain.events.retrofit_completion_events import (
    RakeRetrofitCompletedEvent,
    WorkshopReadyForPickupEvent,
)
from shared.domain.events.wagon_lifecycle_events import (
    BatchRetrofittedEvent,
    WagonReadyForRetrofitEvent,
    WagonRetrofitCompletedEvent,
    WagonRetrofittedEvent,
)
from shared.domain.services.rake_formation_service import RakeFormationService
from shared.domain.services.rake_registry import RakeRegistry
from shared.domain.value_objects.rake_type import RakeType
from shared.infrastructure.time_converters import to_ticks

from .ports.popup_context_port import PopUpContextPort


class PopUpRetrofitContext(PopUpContextPort):
    """PopUp Retrofit Context for managing DAC installation operations."""

    def __init__(
        self, event_bus: EventBus, rake_registry: RakeRegistry | None = None
    ) -> None:
        """Initialize PopUp retrofit context."""
        self._workshops: dict[str, PopUpWorkshop] = {}
        self._event_bus = event_bus
        self.infra = None
        self.scenario = None
        self._workshop_resources = {}
        self._batch_tracking = {}  # Track batch completion
        self._rake_tracking = {}  # Track rake completion
        self.rake_registry = rake_registry or RakeRegistry()
        self._event_handlers: list = []
        # Domain service - pure business logic
        self._processing_service = WorkshopProcessingService()
        # Track bay utilization
        self._bay_status_history: dict[str, list[tuple[float, bool]]] = {}
        # Track bay assignments per workshop
        self._bay_counters: dict[str, int] = {}

    def initialize(self, infra: Any, scenario: Any) -> None:
        """Initialize with infrastructure and scenario."""
        # Prevent re-initialization
        if self.infra is not None:
            return
            
        self.infra = infra
        self.scenario = scenario

        # Create SimPy resources and workshop entities
        if hasattr(scenario, "workshops") and scenario.workshops:
            for workshop in scenario.workshops:
                capacity = getattr(workshop, "retrofit_stations", 1)
                track = getattr(workshop, "track", "unknown")
                self._workshop_resources[workshop.id] = infra.engine.create_resource(
                    capacity
                )
                # Create workshop entity for metrics tracking
                self.create_workshop(workshop.id, track, capacity)

    def start_processes(self) -> None:
        """Start retrofit processes."""
        # Subscribe to wagon ready events
        self._event_bus.subscribe(WagonReadyForRetrofitEvent, self._handle_wagon_ready)

        # Subscribe to rake transported events
        self._event_bus.subscribe(RakeTransportedEvent, self._handle_rake_transported)

        # Subscribe to rake retrofit completion for pickup coordination
        self._event_bus.subscribe(
            RakeRetrofitCompletedEvent, self._handle_rake_retrofit_completed
        )

    def create_workshop(self, workshop_id: str, location: str, num_bays: int) -> None:
        """Create a new PopUp workshop."""
        # Skip track-based IDs (these are tracks, not workshops)
        if workshop_id.startswith('track_'):
            return
            
        # Prevent duplicate creation
        if workshop_id in self._workshops:
            return
            
        # Create retrofit bays
        bays = [
            RetrofitBay(id=BayId(value=f"{workshop_id}_bay_{i}"))
            for i in range(num_bays)
        ]

        workshop = PopUpWorkshop(
            workshop_id=WorkshopId(value=workshop_id),
            location=location,
            retrofit_bays=bays,
        )

        self._workshops[workshop_id] = workshop

    def start_workshop_operations(self, workshop_id: str) -> None:
        """Start operations for a workshop."""
        workshop = self._workshops.get(workshop_id)
        if workshop:
            workshop.start_operations()

    def process_wagon_retrofit(
        self, workshop_id: str, wagon_id: str, current_time: float
    ) -> RetrofitResult:
        """Process wagon retrofit at specified workshop."""
        workshop = self._workshops.get(workshop_id)
        if not workshop:
            return RetrofitResult.failed(
                wagon_id=wagon_id, reason=f"Workshop {workshop_id} not found"
            )

        result, events = workshop.process_wagon(wagon_id, current_time)

        # Publish domain events
        for event in events:
            self._event_bus.publish(event)

        return result

    def get_workshop_metrics(self, workshop_id: str) -> dict[str, Any] | None:
        """Get performance metrics for a workshop."""
        workshop = self._workshops.get(workshop_id)
        if not workshop:
            return None
        return workshop.get_performance_summary()

    def _process_wagon_retrofit(self, wagon: Any, workshop_id: str) -> Any:
        """Process wagon retrofit with SimPy resource management (hybrid approach)."""

        def retrofit_gen():
            workshop_resource = self._workshop_resources.get(workshop_id)
            if not workshop_resource:
                return

            self.infra.engine.current_time()

            # SimPy coordination: request workshop station
            req = workshop_resource.request()
            yield req

            acquire_time = self.infra.engine.current_time()

            # Start retrofit
            wagon.retrofit_start_time = acquire_time
            wagon.status = "RETROFITTING"

            # Assign to next available bay (round-robin)
            if workshop_id not in self._bay_counters:
                self._bay_counters[workshop_id] = 0
            bay_num = self._bay_counters[workshop_id] % workshop_resource.capacity
            self._bay_counters[workshop_id] += 1
            
            bay_id = f"{workshop_id}_bay_{bay_num}"
            if bay_id not in self._bay_status_history:
                self._bay_status_history[bay_id] = []
            self._bay_status_history[bay_id].append((acquire_time, True))
            
            # Store bay_id and request on wagon for later release after pickup
            wagon._assigned_bay_id = bay_id
            wagon._workshop_request = req
            wagon._workshop_resource = workshop_resource

            # Log retrofit start
            try:
                from infrastructure.logging import get_process_logger

                plog = get_process_logger()
                plog.log(
                    f"RETROFIT: Wagon {wagon.id} started at {workshop_id}",
                    sim_time=acquire_time,
                )
            except RuntimeError:
                pass

            # Publish retrofit started event
            from contexts.popup_retrofit.domain.events.retrofit_events import (
                RetrofitStartedEvent,
            )

            start_event = RetrofitStartedEvent(
                wagon_id=wagon.id,
                workshop_id=workshop_id,
                bay_id=f"{workshop_id}_bay_1",
                event_timestamp=acquire_time,
            )
            self._event_bus.publish(start_event)

            # Wait for retrofit completion
            retrofit_time = to_ticks(timedelta(minutes=10))  # Default
            if self.scenario and hasattr(self.scenario, "process_times"):
                process_time = getattr(
                    self.scenario.process_times,
                    "wagon_retrofit_time",
                    timedelta(minutes=10),
                )
                retrofit_time = (
                    to_ticks(process_time)
                    if hasattr(process_time, "total_seconds")
                    else process_time
                )

            yield from self.infra.engine.delay(retrofit_time)

            # Complete retrofit
            complete_time = self.infra.engine.current_time()
            wagon.status = "RETROFITTED"
            wagon.retrofit_end_time = complete_time

            # Track bay idle
            bay_id = getattr(wagon, '_assigned_bay_id', f"{workshop_id}_bay_0")
            self._bay_status_history[bay_id].append((complete_time, False))

            # Log retrofit completion
            try:
                from infrastructure.logging import get_process_logger

                plog = get_process_logger()
                duration = complete_time - acquire_time
                plog.log(
                    f"RETROFIT: Wagon {wagon.id} completed at {workshop_id} (duration={duration:.1f}min)",
                    sim_time=complete_time,
                )
            except RuntimeError:
                pass

            # Publish completion event
            completion_event = WagonRetrofitCompletedEvent(
                wagon_id=wagon.id,
                completion_time=complete_time,
                workshop_id=workshop_id,
                event_timestamp=complete_time,
            )
            self._event_bus.publish(completion_event)

            # Track batch completion - triggers pickup
            self._track_batch_completion(wagon, workshop_id)
            self._track_rake_completion(wagon, workshop_id)
            
            # Resource will be released after wagon is picked up (in yard context)

        return retrofit_gen()

    def _track_batch_completion(self, wagon: Any, workshop_id: str) -> None:
        """Track batch completion and publish domain events."""
        batch_id = getattr(wagon, "batch_id", f"single_{wagon.id}")

        if batch_id not in self._batch_tracking:
            self._batch_tracking[batch_id] = {
                "wagons": [],
                "completed": [],
                "workshop_id": workshop_id,
            }

        batch_info = self._batch_tracking[batch_id]
        if wagon not in batch_info["wagons"]:
            batch_info["wagons"].append(wagon)

        if wagon not in batch_info["completed"]:
            batch_info["completed"].append(wagon)

        # For MVP compatibility: trigger individual wagon pickup for each completed wagon
        individual_event = WagonRetrofittedEvent(
            wagon=wagon,
            workshop_id=workshop_id,
            event_timestamp=self.infra.engine.current_time(),
        )
        self._event_bus.publish(individual_event)

        # Check if batch is complete
        if len(batch_info["completed"]) == len(batch_info["wagons"]):
            # Publish batch event for final cleanup
            event = BatchRetrofittedEvent(
                wagons=batch_info["completed"],
                workshop_id=workshop_id,
                batch_id=batch_id,
                event_timestamp=self.infra.engine.current_time(),
            )
            self._event_bus.publish(event)

            # Clean up tracking
            del self._batch_tracking[batch_id]

    def _track_rake_completion(self, wagon: Any, workshop_id: str) -> None:
        """Track rake completion and publish coordination events."""
        rake_id = getattr(wagon, "rake_id", None)
        if not rake_id or rake_id not in self._rake_tracking:
            # Handle individual wagons - check if workshop is ready for pickup
            self._check_workshop_pickup_readiness(workshop_id)
            return

        rake_info = self._rake_tracking[rake_id]
        if wagon not in rake_info["completed_wagons"]:
            rake_info["completed_wagons"].append(wagon)

        # Check if rake is complete
        if len(rake_info["completed_wagons"]) == rake_info["total_wagons"]:
            current_time = self.infra.engine.current_time()

            # Publish rake retrofit completed event for pickup coordination
            rake_completion_event = RakeRetrofitCompletedEvent(
                rake_id=rake_id,
                workshop_id=workshop_id,
                completed_wagons=rake_info["completed_wagons"],
                completion_time=current_time,
            )
            self._event_bus.publish(rake_completion_event)

            # Clean up tracking
            del self._rake_tracking[rake_id]

    def _check_workshop_pickup_readiness(self, workshop_id: str) -> None:
        """Check if workshop has enough wagons ready for pickup."""
        # Simple threshold - trigger pickup when 2+ wagons are ready
        workshop_resource = self._workshop_resources.get(workshop_id)
        if not workshop_resource:
            return

        # Count completed wagons for this workshop
        completed_count = 0
        ready_wagons = []

        # This is simplified - in practice would track completed wagons per workshop
        if completed_count >= 2:  # Threshold for pickup
            pickup_event = WorkshopReadyForPickupEvent(
                workshop_id=workshop_id,
                ready_wagons=ready_wagons,
                wagon_count=completed_count,
            )
            self._event_bus.publish(pickup_event)

    def get_all_workshop_metrics(self) -> dict[str, dict[str, Any]]:
        """Get performance metrics for all workshops."""
        return {
            workshop_id: workshop.get_performance_summary()
            for workshop_id, workshop in self._workshops.items()
        }

    def _handle_wagon_ready(self, event) -> None:
        """Handle wagon ready for retrofit event using DDD approach."""
        self.infra.engine.current_time()

        # Use domain service to create processing plan
        workshop_capacity = self._get_workshop_capacity(event.workshop_id)
        processing_plan = self._processing_service.create_processing_plan(
            [event.wagon],
            event.workshop_id,
            workshop_capacity,
            ProcessingStrategy.INDIVIDUAL,
        )

        # Validate processing feasibility
        is_feasible, _issues = self._processing_service.validate_processing_feasibility(
            processing_plan, workshop_capacity
        )

        if not is_feasible:
            return

        # Execute processing plan
        self._execute_processing_plan(processing_plan)

    def _handle_rake_transported(self, event: RakeTransportedEvent) -> None:
        """Handle rake transported event using DDD approach."""
        rake = self.rake_registry.get_rake(event.rake_id)
        if not rake or rake.rake_type != RakeType.WORKSHOP_RAKE:
            return

        current_time = self.infra.engine.current_time()

        # Use domain service to create processing plan
        workshop_capacity = self._get_workshop_capacity(event.to_track)
        processing_plan = self._processing_service.create_processing_plan(
            rake.wagons, event.to_track, workshop_capacity, ProcessingStrategy.RAKE
        )

        # Validate processing feasibility
        is_feasible, _issues = self._processing_service.validate_processing_feasibility(
            processing_plan, workshop_capacity
        )

        if not is_feasible:
            return

        # Initialize rake tracking
        self._rake_tracking[event.rake_id] = {
            "total_wagons": rake.wagon_count,
            "completed_wagons": [],
            "workshop_id": event.to_track,
            "start_time": current_time,
        }

        # Publish rake processing started event
        processing_event = RakeProcessingStartedEvent(
            rake_id=event.rake_id,
            workshop_id=event.to_track,
            wagon_count=rake.wagon_count,
        )
        self._event_bus.publish(processing_event)

        # Execute processing plan
        self._execute_processing_plan(processing_plan)

    def _process_rake_batch(self, rake: Any, workshop_id: str) -> Any:
        """Process entire rake as a batch at workshop."""
        workshop_resource = self._workshop_resources.get(workshop_id)
        if not workshop_resource:
            return

        self.infra.engine.current_time()

        # Request workshop stations for entire rake
        requests = []
        for _ in range(rake.wagon_count):
            req = workshop_resource.request()
            requests.append(req)
            yield req

        acquire_time = self.infra.engine.current_time()

        # Process all wagons in parallel
        processes = []
        for wagon in rake.wagons:
            wagon.track = workshop_id
            wagon.status = "RETROFITTING"
            wagon.retrofit_start_time = acquire_time

            # Schedule individual wagon processing
            process = self.infra.engine.schedule_process(
                self._process_single_wagon_in_rake(wagon, workshop_id)
            )
            processes.append(process)

        # Wait for all wagons to complete
        for process in processes:
            yield process

        # Release all workshop stations
        for req in requests:
            workshop_resource.release(req)

        self.infra.engine.current_time()

    def _process_single_wagon_in_rake(self, wagon: Any, workshop_id: str) -> Any:
        """Process single wagon within a rake batch."""
        # Get retrofit time
        retrofit_time = to_ticks(timedelta(minutes=10))  # Default
        if self.scenario and hasattr(self.scenario, "process_times"):
            process_time = getattr(
                self.scenario.process_times,
                "wagon_retrofit_time",
                timedelta(minutes=10),
            )
            retrofit_time = (
                to_ticks(process_time)
                if hasattr(process_time, "total_seconds")
                else process_time
            )

        # Wait for retrofit completion
        yield from self.infra.engine.delay(retrofit_time)

        # Complete retrofit
        complete_time = self.infra.engine.current_time()
        wagon.status = "RETROFITTED"
        wagon.retrofit_end_time = complete_time

        # Publish completion events
        completion_event = WagonRetrofitCompletedEvent(
            wagon_id=wagon.id, completion_time=complete_time, workshop_id=workshop_id
        )
        self._event_bus.publish(completion_event)

        # Track completion
        self._track_batch_completion(wagon, workshop_id)
        self._track_rake_completion(wagon, workshop_id)

    def _handle_rake_retrofit_completed(
        self, event: RakeRetrofitCompletedEvent
    ) -> None:
        """Handle rake retrofit completion - trigger pickup process."""
        self.infra.engine.current_time()

        # Form retrofitted rake for pickup
        formation_service = RakeFormationService()

        retrofitted_rake = formation_service.form_retrofitted_rake(
            event.completed_wagons, event.workshop_id
        )

        # Register rake and publish transport request
        self.rake_registry.register_rake(retrofitted_rake)

        transport_event = RakeTransportRequestedEvent(
            rake_id=retrofitted_rake.rake_id,
            from_track=event.workshop_id,
            to_track="retrofitted",
            rake_type=retrofitted_rake.rake_type,
        )
        self._event_bus.publish(transport_event)

    def _get_workshop_capacity(self, workshop_id: str) -> int:
        """Get workshop capacity from resources."""
        workshop_resource = self._workshop_resources.get(workshop_id)
        if workshop_resource:
            return workshop_resource.capacity
        return 1  # Default capacity

    def _execute_processing_plan(self, processing_plan: Any) -> None:
        """Execute processing plan using application service coordination."""
        for group in processing_plan.wagon_groups:
            if processing_plan.processing_strategy == ProcessingStrategy.INDIVIDUAL:
                for wagon in group:
                    self.infra.engine.schedule_process(
                        self._process_wagon_retrofit(wagon, processing_plan.workshop_id)
                    )
            else:
                # Batch or rake processing
                self.infra.engine.schedule_process(
                    self._process_wagon_group(group, processing_plan.workshop_id)
                )

    def _process_wagon_group(self, wagons: list[Any], workshop_id: str) -> Any:
        """Process group of wagons together."""
        workshop_resource = self._workshop_resources.get(workshop_id)
        if not workshop_resource:
            return

        # Request stations for entire group
        requests = []
        for _ in range(len(wagons)):
            req = workshop_resource.request()
            requests.append(req)
            yield req

        # Process all wagons in parallel
        processes = []
        for wagon in wagons:
            process = self.infra.engine.schedule_process(
                self._process_single_wagon_in_rake(wagon, workshop_id)
            )
            processes.append(process)

        # Wait for completion
        for process in processes:
            yield process

        # Release stations
        for req in requests:
            workshop_resource.release(req)

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics."""
        utilization = self._calculate_workshop_utilization()
        per_workshop = self._calculate_per_workshop_utilization()
        per_bay = self._calculate_per_bay_utilization()
        
        # Filter out track-based workshop entries (only count actual workshops)
        actual_workshops = {k: v for k, v in self._workshops.items() if not k.startswith('track_')}
        
        return {
            "workshops": len(actual_workshops),
            "total_bays": sum(len(w.retrofit_bays) for w in actual_workshops.values()),
            "utilization_percentage": utilization,
            "per_workshop_utilization": per_workshop,
            "per_bay_utilization": per_bay,
        }

    def _calculate_workshop_utilization(self) -> float:
        """Calculate time-weighted workshop utilization."""
        per_workshop = self._calculate_per_workshop_utilization()
        if not per_workshop:
            return 0.0
        
        # Filter out track-based workshops (only count actual workshops)
        actual_workshops = {k: v for k, v in per_workshop.items() if not k.startswith('track_')}
        if not actual_workshops:
            return 0.0
        
        # Average utilization across actual workshops only
        return sum(actual_workshops.values()) / len(actual_workshops)

    def _calculate_per_workshop_utilization(self) -> dict[str, float]:
        """Calculate utilization per workshop (average of all bays)."""
        if not self.infra or not self._bay_status_history:
            return {}

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return {}

        workshop_utilization = {}

        for workshop_id, workshop in self._workshops.items():
            # Calculate average utilization across all bays in this workshop
            bay_utils = []
            for bay_id, history in self._bay_status_history.items():
                if bay_id.startswith(workshop_id):
                    busy_time = 0.0
                    for i in range(0, len(history), 2):
                        if i + 1 < len(history):
                            start_time = history[i][0]
                            end_time = history[i + 1][0]
                            busy_time += end_time - start_time
                    
                    bay_util = (busy_time / total_time) * 100.0 if total_time > 0 else 0.0
                    bay_utils.append(bay_util)
            
            # Average utilization across all bays
            workshop_utilization[workshop_id] = (
                sum(bay_utils) / len(bay_utils) if bay_utils else 0.0
            )

        return workshop_utilization
    
    def _calculate_per_bay_utilization(self) -> dict[str, float]:
        """Calculate utilization per bay."""
        if not self.infra or not self._bay_status_history:
            return {}

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return {}

        bay_utilization = {}

        for bay_id, history in self._bay_status_history.items():
            busy_time = 0.0
            for i in range(0, len(history), 2):
                if i + 1 < len(history):
                    start_time = history[i][0]
                    end_time = history[i + 1][0]
                    busy_time += end_time - start_time
            
            bay_utilization[bay_id] = (
                (busy_time / total_time) * 100.0 if total_time > 0 else 0.0
            )

        return bay_utilization

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {"status": "ready"}

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
