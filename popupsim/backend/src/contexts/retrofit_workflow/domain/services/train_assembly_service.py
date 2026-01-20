"""Train assembly service for multi-rake locomotive operations.

This module provides domain services for assembling trains with multiple rakes,
including proper coupling times, brake testing, and technical inspection.
"""

from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.services.coupling_validation_service import CouplingValidationService
from shared.infrastructure.time_converters import to_ticks


class TrainAssemblyService:
    """Domain service for multi-rake train assembly operations.

    This service handles the complete train assembly workflow including:
    - Rake-to-locomotive coupling with proper timing
    - Brake continuity checks after each rake
    - Final brake test and technical inspection
    - Assembly validation and completion
    """

    def __init__(self) -> None:
        """Initialize the train assembly service."""
        self.coupling_validator = CouplingValidationService()

    def calculate_rake_assembly_time(self, rake: Rake, wagon_repository, process_times: ProcessTimes) -> float:
        """Calculate time to assemble one rake to locomotive.

        Includes coupling time based on coupler types and brake continuity check.

        Parameters
        ----------
        rake : Rake
            Rake being assembled
        wagon_repository
            Repository to resolve wagon entities
        process_times : ProcessTimes
            Process timing configuration

        Returns
        -------
        float
            Total assembly time in simulation ticks
        """
        coupler_type = rake.get_coupling_coupler_type(wagon_repository)
        coupling_time = process_times.get_coupling_ticks(coupler_type)
        continuity_check = to_ticks(process_times.brake_continuity_check_time)

        return coupling_time + continuity_check

    def calculate_final_assembly_time(self, process_times: ProcessTimes) -> float:
        """Calculate time for final train assembly completion.

        Includes full brake test and technical inspection.

        Parameters
        ----------
        process_times : ProcessTimes
            Process timing configuration

        Returns
        -------
        float
            Total final assembly time in simulation ticks
        """
        brake_test_time = to_ticks(process_times.full_brake_test_time)
        inspection_time = to_ticks(process_times.technical_inspection_time)

        return brake_test_time + inspection_time

    def can_assemble_multiple_rakes_to_locomotive(
        self, locomotive: Locomotive, rakes: list[Rake], wagon_repository
    ) -> tuple[bool, str | None]:
        """Validate if multiple rakes can be assembled to locomotive.

        Checks locomotive-to-first-rake and rake-to-rake compatibility.

        Parameters
        ----------
        locomotive : Locomotive
            Locomotive to assemble rakes to
        rakes : list[Rake]
            Ordered list of rakes to be assembled
        wagon_repository
            Repository to resolve wagon entities

        Returns
        -------
        tuple[bool, str | None]
            A tuple containing:
            - bool: True if assembly is possible, False otherwise
            - str | None: Error message if assembly fails, None if successful
        """
        if not rakes:
            return False, 'No rakes provided'

        # Validate locomotive to first rake
        can_couple_first, error = self.can_assemble_rake_to_locomotive(locomotive, rakes[0], wagon_repository)
        if not can_couple_first:
            return False, error

        # Validate rake-to-rake connections for multiple rakes
        if len(rakes) > 1:
            for i in range(len(rakes) - 1):
                rake1 = rakes[i]
                rake2 = rakes[i + 1]

                try:
                    last_wagon_rake1 = wagon_repository.get_by_id(rake1.wagon_ids[-1])
                    first_wagon_rake2 = wagon_repository.get_by_id(rake2.wagon_ids[0])

                    # Check if last wagon of rake1 can couple to first wagon of rake2
                    if not self.coupling_validator.can_couple_wagons(last_wagon_rake1, first_wagon_rake2):
                        return False, (
                            f'Rake {rake1.id} last wagon {last_wagon_rake1.id} '
                            f'incompatible with rake {rake2.id} first wagon {first_wagon_rake2.id}'
                        )
                except ValueError as e:
                    return False, str(e)

        return True, None

    def can_assemble_rake_to_locomotive(
        self, locomotive: Locomotive, rake: Rake, wagon_repository
    ) -> tuple[bool, str | None]:
        """Validate if rake can be assembled to locomotive.

        Checks coupler compatibility between locomotive and first wagon of rake.

        Parameters
        ----------
        locomotive : Locomotive
            Locomotive to assemble rake to
        rake : Rake
            Rake to be assembled
        wagon_repository
            Repository to resolve wagon entities

        Returns
        -------
        tuple[bool, str | None]
            A tuple containing:
            - bool: True if assembly is possible, False otherwise
            - str | None: Error message if assembly fails, None if successful
        """
        try:
            first_wagon = rake.get_first_wagon(wagon_repository)
        except ValueError as e:
            return False, str(e)

        # Check if locomotive can couple to first wagon
        if not self.coupling_validator.can_couple_loco_to_first_wagon(locomotive, first_wagon):
            return False, (
                f'Locomotive {locomotive.id} coupler incompatible with rake {rake.id} first wagon {first_wagon.id}'
            )

        return True, None
