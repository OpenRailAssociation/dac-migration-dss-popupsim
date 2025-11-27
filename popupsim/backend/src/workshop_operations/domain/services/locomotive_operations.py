"""Locomotive business logic - no simulation dependencies."""

from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.locomotive import LocoStatus


class LocomotiveStateManager:
    """Manages locomotive state transitions."""

    @staticmethod
    def mark_moving(loco: Locomotive, current_time: float) -> None:
        """Mark locomotive as moving."""
        loco.record_status_change(current_time, LocoStatus.MOVING)

    @staticmethod
    def mark_coupling(loco: Locomotive, current_time: float) -> None:
        """Mark locomotive as coupling."""
        loco.record_status_change(current_time, LocoStatus.COUPLING)

    @staticmethod
    def mark_decoupling(loco: Locomotive, current_time: float) -> None:
        """Mark locomotive as decoupling."""
        loco.record_status_change(current_time, LocoStatus.DECOUPLING)

    @staticmethod
    def mark_parking(loco: Locomotive, current_time: float) -> None:
        """Mark locomotive as parking."""
        loco.record_status_change(current_time, LocoStatus.PARKING)

    @staticmethod
    def update_location(loco: Locomotive, track_id: str) -> None:
        """Update locomotive location."""
        loco.track = track_id
