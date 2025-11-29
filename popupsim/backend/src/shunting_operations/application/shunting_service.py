"""Enhanced shunting service with capacity constraints and operation queues."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
import logging
from typing import Any
from typing import cast

from analytics.domain.events.locomotive_events import LocomotiveStatusChangeEvent
from analytics.domain.value_objects.timestamp import Timestamp
from shunting_operations.domain.entities.shunting_locomotive import CapacityLimits
from shunting_operations.domain.entities.shunting_locomotive import MovementState
from shunting_operations.domain.entities.shunting_locomotive import ShuntingLocomotive
from shunting_operations.domain.entities.shunting_locomotive import ShuntingStatus
from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.locomotive import LocoStatus
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.infrastructure.routing.route_finder import find_route

logger = logging.getLogger(__name__)


class ShuntingService(ABC):
    """Enhanced service for shunting locomotive operations with capacity management.

    This abstract base class defines the interface for shunting operations within
    workshop yards, including locomotive allocation, movement, and coupling operations
    with capacity constraints and operational tracking.
    """

    @abstractmethod
    def allocate_shunting_locomotive(self, popupsim: Any) -> Generator[Any, Any, ShuntingLocomotive]:
        """Allocate enhanced shunting locomotive.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance

        Returns
        -------
        ShuntingLocomotive
            Enhanced locomotive with capacity constraints

        Yields
        ------
        Any
            SimPy events during allocation
        """

    @abstractmethod
    def release_shunting_locomotive(self, popupsim: Any, loco: ShuntingLocomotive) -> Generator[Any]:
        """Release enhanced shunting locomotive.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance
        loco : ShuntingLocomotive
            Locomotive to release

        Yields
        ------
        Any
            SimPy events during release
        """

    @abstractmethod
    def execute_shunting_move(
        self, popupsim: Any, loco: ShuntingLocomotive, from_track: str, to_track: str
    ) -> Generator[Any]:
        """Execute shunting movement with enhanced locomotive.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance
        loco : ShuntingLocomotive
            Locomotive to move
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Yields
        ------
        Any
            SimPy events during movement
        """

    @abstractmethod
    def execute_coupling(
        self, popupsim: Any, loco: ShuntingLocomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any]:
        """Execute coupling with capacity validation.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance
        loco : ShuntingLocomotive
            Locomotive to couple wagons to
        wagon_count : int
            Number of wagons to couple
        coupler_type : CouplerType
            Type of coupler system

        Yields
        ------
        Any
            SimPy events during coupling
        """

    @abstractmethod
    def execute_decoupling(
        self, popupsim: Any, loco: ShuntingLocomotive, wagon_count: int, coupler_type: CouplerType | None = None
    ) -> Generator[Any]:
        """Execute decoupling with capacity tracking.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance
        loco : ShuntingLocomotive
            Locomotive to decouple wagons from
        wagon_count : int
            Number of wagons to decouple
        coupler_type : CouplerType, optional
            Type of coupler system

        Yields
        ------
        Any
            SimPy events during decoupling
        """


class DefaultShuntingService(ShuntingService):
    """Enhanced implementation with capacity constraints and operation queues.

    Parameters
    ----------
    default_wagon_capacity : int, default=20
        Default maximum number of wagons a locomotive can handle
    default_weight_tons : float, default=1000.0
        Default maximum weight capacity in tons
    default_length_m : float, default=300.0
        Default maximum consist length in meters
    default_coupler_types : list[CouplerType], optional
        Supported coupler types. If None, defaults to [HYBRID]
    """

    def __init__(
        self,
        default_wagon_capacity: int = 20,
        default_weight_tons: float = 1000.0,
        default_length_m: float = 300.0,
        default_coupler_types: list[CouplerType] | None = None,
    ) -> None:
        self.default_capacity = CapacityLimits(default_wagon_capacity, default_weight_tons, default_length_m)
        self.default_coupler_types = default_coupler_types or [CouplerType.HYBRID]

    def allocate_shunting_locomotive(self, popupsim: Any) -> Generator[Any, Any, ShuntingLocomotive]:
        """Allocate enhanced shunting locomotive from pool.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing locomotive pool

        Returns
        -------
        ShuntingLocomotive
            Enhanced locomotive with capacity constraints and operation tracking

        Yields
        ------
        Any
            SimPy events during locomotive allocation
        """
        base_loco = cast(Locomotive, (yield popupsim.locomotives.get()))
        popupsim.locomotives.track_allocation(base_loco.id)

        # Create enhanced shunting locomotive with configured defaults
        movement_state = MovementState(current_track=base_loco.track or 'unknown')
        shunting_loco = ShuntingLocomotive(
            base_locomotive=base_loco,
            capacity_limits=self.default_capacity,
            supported_coupler_types=self.default_coupler_types,
            movement_state=movement_state,
        )
        return shunting_loco

    def release_shunting_locomotive(self, popupsim: Any, loco: ShuntingLocomotive) -> Generator[Any]:
        """Release enhanced shunting locomotive to pool.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing locomotive pool
        loco : ShuntingLocomotive
            Enhanced locomotive to release back to pool

        Yields
        ------
        Any
            SimPy events during locomotive release
        """
        # Set locomotive to parking status when released
        current_time = popupsim.sim.current_time()
        loco.base_locomotive.record_status_change(current_time, LocoStatus.PARKING)
        loco.movement_state.shunting_status = ShuntingStatus.IDLE

        # Emit locomotive event for metrics collection
        event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(current_time),
            locomotive_id=loco.id,
            status=LocoStatus.PARKING.value,
        )
        popupsim.metrics.record_event(event)

        popupsim.locomotives.track_release(loco.id)
        yield popupsim.locomotives.put(loco.base_locomotive)

    def execute_shunting_move(
        self, popupsim: Any, loco: ShuntingLocomotive, from_track: str, to_track: str
    ) -> Generator[Any]:
        """Execute enhanced shunting movement with capacity tracking.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : ShuntingLocomotive
            Enhanced locomotive to move
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Yields
        ------
        Any
            SimPy events during movement execution
        """
        start_time = popupsim.sim.current_time()
        loco.base_locomotive.record_status_change(start_time, LocoStatus.MOVING)
        loco.start_movement(to_track)

        # Emit locomotive event for metrics collection
        event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(start_time), locomotive_id=loco.id, status=LocoStatus.MOVING.value
        )
        popupsim.metrics.record_event(event)

        route = find_route(popupsim.scenario.routes, from_track, to_track)
        duration = route.duration if route and route.duration else 0.0

        utilization = loco.get_capacity_utilization()
        logger.info(
            '🚂 SHUNTING: Loco %s starts moving [%s → %s] at t=%.1f (wagons: %d/%d, %.1f%% capacity)',
            loco.id,
            from_track,
            to_track,
            start_time,
            loco.current_load.coupled_wagons,
            loco.capacity_limits.max_wagon_capacity,
            utilization['wagon_utilization'],
        )

        if duration > 0:
            yield popupsim.sim.delay(duration)
            arrival_time = popupsim.sim.current_time()
            logger.info(
                '✓ SHUNTING: Loco %s arrived at %s at t=%.1f (travel time: %.1f min)',
                loco.id,
                to_track,
                arrival_time,
                duration,
            )
        else:
            logger.info('✓ SHUNTING: Loco %s at %s (no travel needed)', loco.id, to_track)

        # Complete movement using enhanced locomotive
        loco.complete_movement()
        arrival_time = popupsim.sim.current_time()
        loco.base_locomotive.record_status_change(arrival_time, LocoStatus.PARKING)

        # Emit parking event for metrics collection
        parking_event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(arrival_time),
            locomotive_id=loco.id,
            status=LocoStatus.PARKING.value,
        )
        popupsim.metrics.record_event(parking_event)

        loco.base_locomotive.track = to_track

    def execute_coupling(
        self, popupsim: Any, loco: ShuntingLocomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any]:
        """Execute coupling with capacity validation and tracking.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : ShuntingLocomotive
            Enhanced locomotive to couple wagons to
        wagon_count : int
            Number of wagons to couple
        coupler_type : CouplerType
            Type of coupler (SCREW, DAC, or HYBRID)

        Yields
        ------
        Any
            SimPy events during coupling operation
        """
        # Validate coupling compatibility
        if not loco.can_couple_wagon(coupler_type):
            logger.warning(
                '⚠️ SHUNTING: Loco %s cannot couple %s wagons (incompatible coupler)', loco.id, coupler_type.value
            )
            return

        # Check capacity constraints (for reporting)
        if loco.current_load.coupled_wagons + wagon_count > loco.capacity_limits.max_wagon_capacity:
            logger.warning(
                '⚠️ SHUNTING: Loco %s would exceed wagon capacity (%d + %d > %d)',
                loco.id,
                loco.current_load.coupled_wagons,
                wagon_count,
                loco.capacity_limits.max_wagon_capacity,
            )

        process_times = popupsim.scenario.process_times
        time_per_coupling = process_times.get_coupling_time(coupler_type.value)
        coupling_time = wagon_count * time_per_coupling

        # Only change state if coupling takes time
        if coupling_time > 0:
            current_time = popupsim.sim.current_time()
            loco.base_locomotive.record_status_change(current_time, LocoStatus.COUPLING)
            loco.movement_state.shunting_status = ShuntingStatus.COUPLING

            # Emit locomotive event for metrics collection
            event = LocomotiveStatusChangeEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                locomotive_id=loco.id,
                status=LocoStatus.COUPLING.value,
            )
            popupsim.metrics.record_event(event)

            logger.info(
                '🔗 SHUNTING: Loco %s coupling %d wagons (%s) for %.1f min',
                loco.id,
                wagon_count,
                coupler_type.value,
                coupling_time,
            )
            yield popupsim.sim.delay(coupling_time)

            # Update capacity tracking
            loco.current_load.coupled_wagons += wagon_count
            loco.movement_state.shunting_status = ShuntingStatus.IDLE

    def execute_decoupling(
        self, popupsim: Any, loco: ShuntingLocomotive, wagon_count: int, coupler_type: CouplerType | None = None
    ) -> Generator[Any]:
        """Execute decoupling with capacity tracking.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : ShuntingLocomotive
            Enhanced locomotive to decouple wagons from
        wagon_count : int
            Number of wagons to decouple
        coupler_type : CouplerType, optional
            Type of coupler. If None, defaults to SCREW type

        Yields
        ------
        Any
            SimPy events during decoupling operation
        """
        # Validate we have wagons to decouple
        if loco.current_load.coupled_wagons < wagon_count:
            logger.warning(
                '⚠️ SHUNTING: Loco %s cannot decouple %d wagons (only has %d)',
                loco.id,
                wagon_count,
                loco.current_load.coupled_wagons,
            )
            return

        process_times = popupsim.scenario.process_times
        if coupler_type:
            time_per_coupling = process_times.get_decoupling_time(coupler_type.value)
        else:
            time_per_coupling = process_times.screw_decoupling_time  # Default to screw
        decoupling_time = wagon_count * time_per_coupling

        # Only change state if decoupling takes time
        if decoupling_time > 0:
            current_time = popupsim.sim.current_time()
            loco.base_locomotive.record_status_change(current_time, LocoStatus.DECOUPLING)
            loco.movement_state.shunting_status = ShuntingStatus.DECOUPLING

            # Emit locomotive event for metrics collection
            event = LocomotiveStatusChangeEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                locomotive_id=loco.id,
                status=LocoStatus.DECOUPLING.value,
            )
            popupsim.metrics.record_event(event)

            logger.info('🔓 SHUNTING: Loco %s decoupling %d wagons for %.1f min', loco.id, wagon_count, decoupling_time)
            yield popupsim.sim.delay(decoupling_time)

            # Update capacity tracking
            loco.current_load.coupled_wagons -= wagon_count
            loco.movement_state.shunting_status = ShuntingStatus.IDLE
