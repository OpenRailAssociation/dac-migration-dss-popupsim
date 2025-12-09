"""Shunting Operations Context implementation."""

from datetime import timedelta
from typing import Any

from contexts.shunting_operations.domain.aggregates.locomotive_pool import (
    LocomotivePool,
)
from contexts.shunting_operations.domain.entities.shunting_locomotive import (
    ShuntingLocomotive,
)
from contexts.shunting_operations.domain.services.rake_transport_service import (
    RakeTransportService,
)
from contexts.shunting_operations.domain.value_objects.locomotive_id import (
    LocomotiveId,
)
from infrastructure.event_bus.event_bus import EventBus
from shared.domain.events.rake_events import (
    RakeTransportedEvent,
    RakeTransportRequestedEvent,
)
from shared.domain.events.wagon_lifecycle_events import (
    LocomotiveMovementRequestEvent,
)
from shared.domain.resource_status import LocoStatus
from shared.domain.services.rake_formation_service import RakeFormationService
from shared.domain.services.rake_registry import RakeRegistry
from shared.infrastructure.time_converters import to_ticks

from shared.infrastructure.track_resource_manager import TrackResourceManager

from .locomotive_status_tracker import LocomotiveStatusTracker
from .ports.shunting_context_port import ShuntingContextPort


class ShuntingOperationsContext(ShuntingContextPort):
    """Shunting Operations Context for locomotive management."""

    def __init__(
        self, event_bus: EventBus, rake_registry: RakeRegistry | None = None
    ) -> None:
        """Initialize shunting operations context."""
        self._locomotive_pool = LocomotivePool(locomotives=[])
        self._event_bus = event_bus
        self.infra = None
        self.scenario = None
        self._allocated_locos: dict[str, ShuntingLocomotive] = {}
        self.status_tracker = LocomotiveStatusTracker()
        self._simpy_locomotive_store = None  # SimPy store for hybrid approach
        self.rake_registry = rake_registry or RakeRegistry()
        self._rake_transport_service = None  # Will be initialized after self is created
        self._event_handlers: list = []
        self.track_resource_manager: TrackResourceManager | None = None

    def initialize(self, infra: Any, scenario: Any) -> None:
        """Initialize with infrastructure and scenario."""
        self.infra = infra
        self.scenario = scenario

        # Create locomotives from scenario
        if scenario.locomotives:
            for loco_dto in scenario.locomotives:
                self.add_locomotive(loco_dto.id, loco_dto.track)

        # Create SimPy store for hybrid locomotive management
        if self._locomotive_pool.locomotives:
            self._simpy_locomotive_store = infra.engine.create_store(
                capacity=len(self._locomotive_pool.locomotives)
            )
            # Add all locomotives to SimPy store
            for loco in self._locomotive_pool.locomotives:
                self._simpy_locomotive_store.put(loco)

        # Initialize track resource manager
        if scenario.tracks:
            loco_count = len(scenario.locomotives) if scenario.locomotives else 3
            self.track_resource_manager = TrackResourceManager(
                infra.engine, scenario.tracks, loco_count
            )

        # Initialize rake transport service
        self._rake_transport_service = RakeTransportService(self)

    def start_processes(self) -> None:
        """Start shunting processes."""
        # Initialize all locomotives as PARKING at t=0
        for loco in self._locomotive_pool.locomotives:
            self.status_tracker.record_status_change(
                loco.id.value, 0.0, LocoStatus.PARKING
            )

        # Subscribe to locomotive movement requests
        self._event_bus.subscribe(
            LocomotiveMovementRequestEvent, self._handle_movement_request
        )

        # Subscribe to rake transport requests
        self._event_bus.subscribe(
            RakeTransportRequestedEvent, self._handle_rake_transport_request
        )

        # Start initial locomotive movement at t=0.0
        if self.infra and self.infra.engine:
            self.infra.engine.schedule_process(self._start_initial_movement())

    def add_locomotive(
        self, locomotive_id: str, track: str, capacity: int = 10
    ) -> None:
        """Add a locomotive to the pool."""
        locomotive = ShuntingLocomotive(
            id=LocomotiveId(value=locomotive_id),
            current_track=track,
            home_track=track,
            max_capacity=capacity,
        )
        self._locomotive_pool.locomotives.append(locomotive)

    def allocate_locomotive(self, context: Any) -> Any:
        """Allocate locomotive using SimPy store (hybrid approach)."""

        def allocate_gen():
            if self._simpy_locomotive_store:
                # Use SimPy store for natural queuing and blocking
                loco = yield self._simpy_locomotive_store.get()
                self._allocated_locos[loco.id.value] = loco
                loco.status = "MOVING"

                # Publish event
                from contexts.shunting_operations.domain.events.shunting_events import (
                    LocomotiveAllocatedEvent,
                )

                event = LocomotiveAllocatedEvent(
                    locomotive_id=loco.id.value,
                    allocated_to="yard",
                    track=loco.current_track,
                    event_timestamp=context.infra.engine.current_time(),
                )
                self._event_bus.publish(event)

                return loco
            else:
                # Fallback to original method
                if not self._locomotive_pool.locomotives:
                    msg = "No locomotives available"
                    raise RuntimeError(msg)
                loco = self._locomotive_pool.locomotives[0]
                if loco.id.value not in self._allocated_locos:
                    self._allocated_locos[loco.id.value] = loco
                    loco.status = "MOVING"
                    yield context.infra.engine.delay(0)
                    return loco
                msg = "No locomotives available"
                raise RuntimeError(msg)

        return allocate_gen()

    def release_locomotive(self, context: Any, loco: Any) -> Any:
        """Release locomotive back to SimPy store (hybrid approach)."""

        def release_gen():
            if loco.id.value in self._allocated_locos:
                del self._allocated_locos[loco.id.value]
                loco.status = "IDLE"

                # Record status change to PARKING
                current_time = context.infra.engine.current_time()
                self.status_tracker.record_status_change(
                    loco.id.value, current_time, LocoStatus.PARKING
                )

                # Publish event
                from contexts.shunting_operations.domain.events.shunting_events import (
                    LocomotiveReleasedEvent,
                )

                event = LocomotiveReleasedEvent(
                    locomotive_id=loco.id.value,
                    released_from="yard",
                    track=loco.current_track,
                    event_timestamp=current_time,
                )
                self._event_bus.publish(event)

                if self._simpy_locomotive_store:
                    # Return to SimPy store for natural resource management
                    yield self._simpy_locomotive_store.put(loco)
                else:
                    yield context.infra.engine.delay(0)
            else:
                yield context.infra.engine.delay(0)

        return release_gen()

    def move_locomotive(
        self,
        context: Any,
        loco: Any,
        from_track: str,
        to_track: str,
        wagon_ids: list[str] | None = None,
    ) -> Any:
        """Move locomotive between tracks with track blocking."""

        def move_gen():
            from infrastructure.logging import get_process_logger

            # Record status change at current time
            current_time = context.infra.engine.current_time()
            self.status_tracker.record_status_change(
                loco.id.value, current_time, LocoStatus.MOVING
            )

            # Publish movement started event
            from shared.domain.events.locomotive_events import (
                LocomotiveMovementStartedEvent,
            )

            start_event = LocomotiveMovementStartedEvent(
                locomotive_id=loco.id.value,
                from_track=from_track,
                to_track=to_track,
                event_timestamp=current_time,
            )
            context.infra.event_bus.publish(start_event)

            # Get route and calculate move time
            route_path = self._get_route_path(context, from_track, to_track)
            move_time = self._get_move_time(context, from_track, to_track)

            # Track blocking: only enabled with multiple locomotives
            track_requests = []
            if self.track_resource_manager and len(self._locomotive_pool.locomotives) > 1:
                # Release source track first
                if (
                    hasattr(loco, "track_request")
                    and loco.track_request
                    and from_track in self.track_resource_manager.track_resources
                ):
                    self.track_resource_manager.release_track(from_track, loco.track_request)
                    loco.track_request = None

                # Request tracks in path (blocking)
                for track_id in route_path:
                    if track_id == from_track:
                        continue
                    if track_id not in self.track_resource_manager.track_resources:
                        continue
                    request = yield self.track_resource_manager.request_track(track_id)
                    track_requests.append((track_id, request))

            # Log process with wagon info if available
            try:
                plog = get_process_logger()
                if wagon_ids:
                    wagon_str = ", ".join(wagon_ids)
                    plog.log(
                        f"LOCO {loco.id.value}: Moving {from_track} -> {to_track} with [{wagon_str}] (duration={move_time:.1f}min)",
                        sim_time=current_time,
                    )
                else:
                    plog.log(
                        f"LOCO {loco.id.value}: Moving {from_track} -> {to_track} (duration={move_time:.1f}min)",
                        sim_time=current_time,
                    )
            except RuntimeError:
                pass

            # Delay for movement time
            yield from context.infra.engine.delay(move_time)

            # Update track after movement completes
            loco.current_track = to_track

            # Release intermediate tracks and store destination
            if self.track_resource_manager and len(self._locomotive_pool.locomotives) > 1:
                for track_id, request in track_requests:
                    if track_id != to_track:
                        self.track_resource_manager.release_track(track_id, request)

                for track_id, request in track_requests:
                    if track_id == to_track:
                        loco.track_request = request
                        break

            # Log arrival
            try:
                plog = get_process_logger()
                plog.log(
                    f"LOCO {loco.id.value}: Arrived at {to_track}",
                    sim_time=context.infra.engine.current_time(),
                )
            except RuntimeError:
                pass

            # Publish movement completed event
            from shared.domain.events.locomotive_events import (
                LocomotiveMovementCompletedEvent,
            )

            end_event = LocomotiveMovementCompletedEvent(
                locomotive_id=loco.id.value,
                from_track=from_track,
                to_track=to_track,
                event_timestamp=context.infra.engine.current_time(),
            )
            context.infra.event_bus.publish(end_event)

        return move_gen()

    def _get_route_path(
        self, context: Any, from_track: str, to_track: str
    ) -> list[str]:
        """Get route path between tracks."""
        if context.scenario.routes:
            for route in context.scenario.routes:
                if route.track_sequence and len(route.track_sequence) >= 2:
                    if (
                        route.track_sequence[0] == from_track
                        and route.track_sequence[-1] == to_track
                    ):
                        return route.track_sequence
                    if (
                        route.track_sequence[-1] == from_track
                        and route.track_sequence[0] == to_track
                    ):
                        return list(reversed(route.track_sequence))
        return [from_track, to_track]

    def _get_move_time(self, context: Any, from_track: str, to_track: str) -> float:
        """Get movement time between tracks."""
        move_time = to_ticks(timedelta(minutes=1))  # Default 1 minute
        if context.scenario.routes:
            for route in context.scenario.routes:
                if route.track_sequence and len(route.track_sequence) >= 2:
                    if (
                        route.track_sequence[0] == from_track
                        and route.track_sequence[1] == to_track
                    ) or (
                        route.track_sequence[1] == from_track
                        and route.track_sequence[0] == to_track
                    ):
                        move_time = to_ticks(timedelta(minutes=route.duration))
                        break
        return move_time

    def couple_wagons(
        self,
        context: Any,
        wagon_count: int,
        coupler_type: str,
        wagon_ids: list[str] | None = None,
    ) -> Any:
        """Couple wagons to locomotive."""

        def couple_gen():
            from infrastructure.logging import get_process_logger

            # Get coupling time from scenario
            coupling_time = to_ticks(timedelta(minutes=0.5))  # Default
            if context.scenario.process_times:
                coupling_time = context.scenario.process_times.get_coupling_ticks(
                    coupler_type
                )

            # Track coupling status if time > 0
            current_time = context.infra.engine.current_time()
            if coupling_time > 0:
                for loco in self._locomotive_pool.locomotives:
                    if loco.id.value in self._allocated_locos:
                        self.status_tracker.record_status_change(
                            loco.id.value, current_time, LocoStatus.COUPLING
                        )

            for _ in range(wagon_count):
                yield from context.infra.engine.delay(coupling_time)

            # Return to moving status
            if coupling_time > 0:
                current_time = context.infra.engine.current_time()
                for loco in self._locomotive_pool.locomotives:
                    if loco.id.value in self._allocated_locos:
                        self.status_tracker.record_status_change(
                            loco.id.value, current_time, LocoStatus.MOVING
                        )

            # Log coupling completion
            try:
                plog = get_process_logger()
                if wagon_ids:
                    wagon_str = ", ".join(wagon_ids)
                    plog.log(
                        f"COUPLING: [{wagon_str}] with {coupler_type} couplers (total={wagon_count * coupling_time:.1f}min)",
                        sim_time=context.infra.engine.current_time(),
                    )
                else:
                    plog.log(
                        f"COUPLING: {wagon_count} wagons with {coupler_type} couplers (total={wagon_count * coupling_time:.1f}min)",
                        sim_time=context.infra.engine.current_time(),
                    )
            except RuntimeError:
                pass

        return couple_gen()

    def decouple_wagons(
        self,
        context: Any,
        wagon_count: int,
        coupler_type: str | None = None,
        wagon_ids: list[str] | None = None,
    ) -> Any:
        """Decouple wagons from locomotive."""

        def decouple_gen():
            from infrastructure.logging import get_process_logger

            # Get decoupling time from scenario
            decoupling_time = to_ticks(timedelta(minutes=0.5))  # Default
            if context.scenario.process_times and coupler_type:
                decoupling_time = context.scenario.process_times.get_coupling_ticks(
                    coupler_type
                )

            # Track decoupling status if time > 0
            current_time = context.infra.engine.current_time()
            if decoupling_time > 0:
                for loco in self._locomotive_pool.locomotives:
                    if loco.id.value in self._allocated_locos:
                        self.status_tracker.record_status_change(
                            loco.id.value, current_time, LocoStatus.DECOUPLING
                        )

            for _ in range(wagon_count):
                yield from context.infra.engine.delay(decoupling_time)

            # Return to moving status
            if decoupling_time > 0:
                current_time = context.infra.engine.current_time()
                for loco in self._locomotive_pool.locomotives:
                    if loco.id.value in self._allocated_locos:
                        self.status_tracker.record_status_change(
                            loco.id.value, current_time, LocoStatus.MOVING
                        )

            # Log decoupling completion
            try:
                plog = get_process_logger()
                if wagon_ids:
                    wagon_str = ", ".join(wagon_ids)
                    plog.log(
                        f"DECOUPLING: [{wagon_str}] with {coupler_type or 'SCREW'} couplers (total={wagon_count * decoupling_time:.1f}min)",
                        sim_time=context.infra.engine.current_time(),
                    )
                else:
                    plog.log(
                        f"DECOUPLING: {wagon_count} wagons with {coupler_type or 'SCREW'} couplers (total={wagon_count * decoupling_time:.1f}min)",
                        sim_time=context.infra.engine.current_time(),
                    )
            except RuntimeError:
                pass

        return decouple_gen()

    def get_locomotive_count(self) -> int:
        """Get total number of locomotives."""
        return len(self._locomotive_pool.locomotives)

    def get_available_count(self) -> int:
        """Get number of available locomotives."""
        return self._locomotive_pool.get_available_count()

    def get_utilization(self) -> float:
        """Get locomotive utilization percentage."""
        return self._locomotive_pool.get_utilization()

    def allocate_locomotive_simple(self, purpose: str) -> ShuntingLocomotive | None:
        """Simple locomotive allocation for testing (non-SimPy)."""
        locomotive, events = self._locomotive_pool.allocate_locomotive(purpose, 0.0)

        # Publish events
        for event in events:
            self._event_bus.publish(event)

        return locomotive

    def release_locomotive_simple(self, locomotive_id: str) -> bool:
        """Simple locomotive release for testing (non-SimPy)."""
        success, events = self._locomotive_pool.release_locomotive(locomotive_id, 0.0)

        # Publish events
        for event in events:
            self._event_bus.publish(event)

        return success

    def _handle_movement_request(self, event) -> None:
        """Handle locomotive movement request event."""
        if self.infra and self.infra.engine:
            self.infra.engine.schedule_process(self._execute_movement(event))

    def _execute_movement(self, event) -> Any:
        """Execute locomotive movement for wagon transport."""
        # Allocate locomotive
        loco = yield from self.allocate_locomotive(self)

        try:
            # Move to pickup location
            yield from self.move_locomotive(
                self, loco, loco.current_track, event.from_track
            )

            # Couple wagons
            wagon_ids = [w.id for w in event.wagons] if event.wagons else None
            yield from self.couple_wagons(self, len(event.wagons), "SCREW", wagon_ids)

            # Move to destination
            yield from self.move_locomotive(
                self, loco, event.from_track, event.to_track
            )

            # Decouple wagons
            yield from self.decouple_wagons(self, len(event.wagons), "SCREW", wagon_ids)

            # Return to home track
            home_track = getattr(loco, "home_track", "locoparking")
            yield from self.move_locomotive(self, loco, event.to_track, home_track)

        finally:
            # Release locomotive
            yield from self.release_locomotive(self, loco)

    def get_metrics(self) -> dict[str, Any]:
        """Get shunting operations metrics."""
        utilization = self._calculate_time_weighted_utilization()
        breakdown = self._calculate_utilization_breakdown()
        per_loco = self._calculate_per_locomotive_breakdown()

        return {
            "total_locomotives": len(self._locomotive_pool.locomotives),
            "available_locomotives": self.get_available_count(),
            "allocated_locomotives": len(self._allocated_locos),
            "utilization_percentage": utilization,
            "utilization_breakdown": breakdown,
            "per_locomotive_breakdown": per_loco,
            "total_operations": 0,
            "successful_operations": 0,
            "success_rate": 0.0,
            "average_operation_time": 0.0,
        }

    def _calculate_time_weighted_utilization(self) -> float:
        """Calculate time-weighted utilization from status history."""
        if not self._locomotive_pool.locomotives or not self.infra:
            return 0.0

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return 0.0

        total_busy_time = 0.0

        for loco in self._locomotive_pool.locomotives:
            history = self.status_tracker.get_status_history(loco.id.value)
            if not history:
                continue

            # Calculate time spent in MOVING status
            for i in range(len(history)):
                start_time, status = history[i]

                # Determine end time
                if i + 1 < len(history):
                    end_time = history[i + 1][0]
                else:
                    end_time = total_time

                # Count MOVING time as busy
                if status == LocoStatus.MOVING:
                    total_busy_time += end_time - start_time

        # Calculate utilization percentage
        total_possible_time = total_time * len(self._locomotive_pool.locomotives)
        return (
            (total_busy_time / total_possible_time) * 100.0
            if total_possible_time > 0
            else 0.0
        )

    def _calculate_utilization_breakdown(self) -> dict[str, float]:
        """Calculate breakdown of locomotive time by activity."""
        if not self._locomotive_pool.locomotives or not self.infra:
            return {}

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return {}

        status_times = {
            "MOVING": 0.0,
            "PARKING": 0.0,
            "COUPLING": 0.0,
            "DECOUPLING": 0.0,
        }

        for loco in self._locomotive_pool.locomotives:
            history = self.status_tracker.get_status_history(loco.id.value)
            if not history:
                status_times["PARKING"] += total_time
                continue

            for i in range(len(history)):
                start_time, status = history[i]
                end_time = history[i + 1][0] if i + 1 < len(history) else total_time
                duration = end_time - start_time
                status_name = status.name if hasattr(status, "name") else str(status)

                if status_name not in status_times:
                    status_times[status_name] = 0.0
                status_times[status_name] += duration

        total_possible_time = total_time * len(self._locomotive_pool.locomotives)
        breakdown = {}
        for status, time_spent in status_times.items():
            breakdown[status] = (
                (time_spent / total_possible_time) * 100.0
                if total_possible_time > 0
                else 0.0
            )

        return breakdown

    def _calculate_per_locomotive_breakdown(self) -> dict[str, dict[str, float]]:
        """Calculate breakdown per locomotive."""
        if not self._locomotive_pool.locomotives or not self.infra:
            return {}

        total_time = self.infra.engine.current_time()
        if total_time == 0:
            return {}

        per_loco = {}

        for loco in self._locomotive_pool.locomotives:
            status_times = {
                "MOVING": 0.0,
                "PARKING": 0.0,
                "COUPLING": 0.0,
                "DECOUPLING": 0.0,
            }
            history = self.status_tracker.get_status_history(loco.id.value)

            if not history:
                status_times["PARKING"] = total_time
            else:
                for i in range(len(history)):
                    start_time, status = history[i]
                    end_time = history[i + 1][0] if i + 1 < len(history) else total_time
                    duration = end_time - start_time
                    status_name = (
                        status.name if hasattr(status, "name") else str(status)
                    )

                    if status_name not in status_times:
                        status_times[status_name] = 0.0
                    status_times[status_name] += duration

            breakdown = {}
            for status, time_spent in status_times.items():
                breakdown[status] = (
                    (time_spent / total_time) * 100.0 if total_time > 0 else 0.0
                )

            per_loco[loco.id.value] = breakdown

        return per_loco

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

    def _start_initial_movement(self) -> Any:
        """Start initial locomotive movement triggered by first wagon arrival."""
        yield from self.infra.engine.delay(0)

    def _handle_rake_transport_request(
        self, event: RakeTransportRequestedEvent
    ) -> None:
        """Handle rake transport request event."""
        if self.infra and self.infra.engine:
            self.infra.engine.schedule_process(self._execute_rake_transport(event))

    def _execute_rake_transport(self, event: RakeTransportRequestedEvent) -> Any:
        """Execute rake transport following MVP pattern."""
        rake = self.rake_registry.get_rake(event.rake_id)
        if not rake:
            return

        start_time = self.infra.engine.current_time()

        # Allocate locomotive (MVP pattern)
        loco = yield from self.allocate_locomotive(self)

        try:
            # Move to pickup location
            yield from self.move_locomotive(
                self, loco, loco.current_track, event.from_track
            )

            # Couple rake wagons
            coupler_type = self._determine_coupler_type(rake.wagons)
            wagon_ids = rake.wagon_ids if hasattr(rake, "wagon_ids") else None
            yield from self.couple_wagons(
                self, rake.wagon_count, coupler_type, wagon_ids
            )

            # Transport rake to destination
            yield from self.move_locomotive(
                self, loco, event.from_track, event.to_track
            )

            # Decouple wagons at destination
            yield from self.decouple_wagons(
                self, rake.wagon_count, coupler_type, wagon_ids
            )

            # Return locomotive to home track
            home_track = getattr(loco, "home_track", "locoparking")
            yield from self.move_locomotive(self, loco, event.to_track, home_track)

        finally:
            # Release locomotive
            yield from self.release_locomotive(self, loco)

        end_time = self.infra.engine.current_time()
        transport_duration = end_time - start_time

        # Update rake registry
        self.rake_registry.update_rake_track(event.rake_id, event.to_track)

        # Publish transport completed event
        transport_event = RakeTransportedEvent(
            rake_id=event.rake_id,
            from_track=event.from_track,
            to_track=event.to_track,
            transport_duration=transport_duration,
            wagon_count=rake.wagon_count,
        )
        self._event_bus.publish(transport_event)

    def _determine_coupler_type(self, wagons: list[Any]) -> str:
        """Determine coupler type for rake based on wagon couplers."""
        # If any wagon has DAC, use DAC for the rake
        for wagon in wagons:
            if hasattr(wagon, "coupler_type") and wagon.coupler_type == "DAC":
                return "DAC"
        return "SCREW"

    def _optimize_rake_for_transport(self, rake: Any) -> Any:
        """Optimize rake for transport based on shunting constraints."""
        # Get transport constraints
        locomotive_capacity = 20  # Max wagons per locomotive
        track_capacity = 150.0  # Max track length in meters

        # If rake exceeds locomotive capacity, split it
        if rake.wagon_count > locomotive_capacity:
            # Use fixed size strategy to split rake
            service = RakeFormationService()
            constraints = {
                "rake_size": locomotive_capacity,
                "formation_track": rake.formation_track,
                "rake_type": rake.rake_type,
            }

            split_rakes = service.form_rakes(rake.wagons, "fixed_size", constraints)

            # Register split rakes and return first one
            for split_rake in split_rakes:
                split_rake.target_track = rake.target_track
                self.rake_registry.register_rake(split_rake)

            return split_rakes[0] if split_rakes else rake

        # If rake exceeds track capacity, split by length
        if rake.total_length > track_capacity:
            service = RakeFormationService()
            constraints = {
                "track_capacity": track_capacity,
                "formation_track": rake.formation_track,
                "rake_type": rake.rake_type,
            }

            split_rakes = service.form_rakes(rake.wagons, "track_capacity", constraints)

            # Register split rakes
            for split_rake in split_rakes:
                split_rake.target_track = rake.target_track
                self.rake_registry.register_rake(split_rake)

            return split_rakes[0] if split_rakes else rake

        return rake
