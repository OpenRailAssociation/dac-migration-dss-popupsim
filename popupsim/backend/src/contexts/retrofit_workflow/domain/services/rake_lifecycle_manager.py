"""Rake Lifecycle Manager - Pure domain service for rake operations.

This module provides a domain service for managing the complete lifecycle of
railway rakes without any simulation infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import timedelta

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.coupling_service import CouplingService
from contexts.retrofit_workflow.domain.services.rake_formation_service import RakeFormationService
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest
from shared.infrastructure.simpy_time_converters import sim_ticks_to_timedelta


@dataclass
class RakeFormationContext:
    """Context for rake formation operations."""

    formation_track: str
    target_track: str
    rake_type: RakeType
    formation_time: float


@dataclass
class RakeFormationResult:
    """Result of rake formation operation."""

    rake: Rake | None
    success: bool
    error_message: str | None
    formation_duration: timedelta


@dataclass
class RakeDissolutionResult:
    """Result of rake dissolution operation."""

    wagons: list[Wagon]
    success: bool
    dissolution_duration: timedelta


@dataclass
class ValidationResult:
    """Result of validation operations."""

    is_valid: bool
    error_message: str | None


class RakeLifecycleManager:
    """Pure domain service for rake lifecycle management.

    Manages complete rake lifecycle without SimPy dependencies:
    - Formation with coupling validation
    - Dissolution with proper timing
    - Time calculations for operations
    - Validation of rake constraints

    This service contains only business logic and domain rules.
    """

    def __init__(self, coupling_service: CouplingService) -> None:
        """Initialize with coupling service for time calculations.

        Parameters
        ----------
        coupling_service : CouplingService
            Service for calculating coupling/decoupling times
        """
        self._coupling_service = coupling_service
        self._rake_formation_service = RakeFormationService()

    def form_rake(self, wagons: list[Wagon], context: RakeFormationContext) -> RakeFormationResult:
        """Form rake with coupling validation and timing calculation.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to form into rake (in coupling order)
        context : RakeFormationContext
            Formation context with track and type information

        Returns
        -------
        RakeFormationResult
            Result containing rake or error information
        """
        if not wagons:
            return RakeFormationResult(
                rake=None,
                success=False,
                error_message='Cannot form rake with no wagons',
                formation_duration=timedelta(0),
            )

        # Create formation request
        rake_id = f'RAKE_{context.formation_track}_{len(wagons)}_{id(wagons[0])}'
        request = RakeFormationRequest(
            rake_id=rake_id,
            wagons=wagons,
            rake_type=context.rake_type,
            formation_track=context.formation_track,
            target_track=context.target_track,
            formation_time=context.formation_time,
        )

        # Validate and form rake
        rake, error = self._rake_formation_service.form_rake(request)

        if not rake:
            return RakeFormationResult(rake=None, success=False, error_message=error, formation_duration=timedelta(0))

        # Calculate formation time
        formation_duration = self._calculate_formation_time(wagons)

        return RakeFormationResult(rake=rake, success=True, error_message=None, formation_duration=formation_duration)

    def dissolve_rake(self, rake: Rake, wagons: list[Wagon]) -> RakeDissolutionResult:
        """Dissolve rake and return individual wagons.

        Parameters
        ----------
        rake : Rake
            Rake to dissolve
        wagons : list[Wagon]
            Wagon entities that were part of the rake

        Returns
        -------
        RakeDissolutionResult
            Result containing wagons and dissolution timing
        """
        # Calculate dissolution time before dissolving
        dissolution_duration = self._calculate_dissolution_time(wagons)

        # Dissolve rake (removes associations)
        self._rake_formation_service.dissolve_rake(rake, wagons)

        return RakeDissolutionResult(wagons=wagons, success=True, dissolution_duration=dissolution_duration)

    def validate_rake_formation(self, wagons: list[Wagon]) -> ValidationResult:
        """Validate if wagons can form a valid rake.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to validate for rake formation

        Returns
        -------
        ValidationResult
            Validation result with success/error information
        """
        if not wagons:
            return ValidationResult(is_valid=False, error_message='Cannot validate empty wagon list')

        can_form, error = self._rake_formation_service.can_form_rake(wagons)

        return ValidationResult(is_valid=can_form, error_message=error)

    def calculate_formation_time(self, wagons: list[Wagon]) -> timedelta:
        """Calculate coupling time for rake formation.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to be coupled into rake

        Returns
        -------
        timedelta
            Total time required for coupling operations
        """
        return self._calculate_formation_time(wagons)

    def calculate_dissolution_time(self, wagons: list[Wagon]) -> timedelta:
        """Calculate decoupling time for rake dissolution.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to be decoupled from rake

        Returns
        -------
        timedelta
            Total time required for decoupling operations
        """
        return self._calculate_dissolution_time(wagons)

    def _calculate_formation_time(self, wagons: list[Wagon]) -> timedelta:
        """Calculate formation time using existing coupling service."""
        coupling_ticks = self._coupling_service.get_rake_coupling_time(wagons)
        return sim_ticks_to_timedelta(coupling_ticks)

    def _calculate_dissolution_time(self, wagons: list[Wagon]) -> timedelta:
        """Calculate dissolution time using existing coupling service."""
        decoupling_ticks = self._coupling_service.get_rake_decoupling_time(wagons)
        return sim_ticks_to_timedelta(decoupling_ticks)
