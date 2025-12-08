"""Service for transporting rakes between tracks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    from contexts.shunting_operations.application.shunting_context import (
        ShuntingOperationsContext,
    )
    from shared.domain.entities.rake import Rake


@dataclass
class RakeTransportJob:
    """Transport job for moving a rake between tracks."""

    rake: Rake
    from_track: str
    to_track: str


class RakeTransportService:
    """Service for executing rake transport operations."""

    def __init__(self, shunting_context: ShuntingOperationsContext) -> None:
        self.shunting_context = shunting_context

    def execute_rake_transport(self, job: RakeTransportJob) -> Generator[Any, Any]:
        """Execute transport for entire rake."""
        rake = job.rake

        # Allocate locomotive
        loco = yield from self.shunting_context.allocate_locomotive(
            self.shunting_context
        )

        try:
            # Move to pickup location
            yield from self.shunting_context.move_locomotive(
                self.shunting_context, loco, loco.current_track, job.from_track
            )

            # Couple entire rake
            yield from self.shunting_context.couple_wagons(
                self.shunting_context, loco, rake.wagon_count, "SCREW"
            )

            # Update rake status
            rake.locomotive_id = loco.id.value
            rake.status = "MOVING"

            # Transport rake
            yield from self.shunting_context.move_locomotive(
                self.shunting_context, loco, job.from_track, job.to_track
            )

            # Decouple rake
            yield from self.shunting_context.decouple_wagons(
                self.shunting_context, loco, rake.wagon_count, "SCREW"
            )

            # Update rake and wagon states
            rake.formation_track = job.to_track
            rake.locomotive_id = None
            rake.status = "DELIVERED"
            rake.update_wagon_tracks(job.to_track)

        finally:
            # Release locomotive
            yield from self.shunting_context.release_locomotive(
                self.shunting_context, loco
            )
