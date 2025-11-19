"""Configuration validation module for train simulation scenarios.

This module provides validation logic for scenario configurations, including
workshop tracks, capacity validation, route validation, train schedule validation,
and simulation duration checks. It ensures that loaded configurations are
logically consistent and meet business requirements.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
import logging

from models.scenario import Scenario
from models.track import TrackType

logger = logging.getLogger('validation')


class ValidationLevel(Enum):
    """Severity level of a validation message."""

    ERROR = 'ERROR'  # Indicates a critical issue; simulation cannot start
    WARNING = 'WARNING'  # Indicates a non-critical issue; simulation can start but may be suboptimal
    INFO = 'INFO'  # Provides informational messages for the user


@dataclass
class ValidationIssue:
    """Single validation issue encountered during models validation.

    Attributes
    ----------
        level (ValidationLevel): The severity level of the issue.
        message (str): A descriptive message explaining the issue.
        field (str | None): The specific field affected by the issue, if applicable.
        suggestion (str | None): A suggested resolution for the issue, if available.

    """

    level: ValidationLevel
    message: str
    field: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return a formatted string representation of the validation issue.

        Returns
        -------
        str
            A string describing the issue, including its severity, message,
            affected field (if any), and suggestion (if any).
        """
        result = f'[{self.level.value}] {self.message}'
        if self.field:
            result += f' (Field: {self.field})'
        if self.suggestion:
            result += f'\n  → Suggestion: {self.suggestion}'
        return result


@dataclass
class ValidationResult:
    """Result of a models validation process.

    Attributes
    ----------
        is_valid (bool): Indicates whether the models is valid.
        issues (list[ValidationIssue]): A list of validation issues encountered.

    """

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    level: ValidationLevel = ValidationLevel.INFO

    def has_errors(self) -> bool:
        """Check if there are any validation issues with the ERROR severity level.

        Returns
        -------
        bool
            True if there are ERROR-level issues, False otherwise.
        """
        return any(i.level == ValidationLevel.ERROR for i in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any validation issues with the WARNING severity level.

        Returns
        -------
        bool
            True if there are WARNING-level issues, False otherwise.
        """
        return any(i.level == ValidationLevel.WARNING for i in self.issues)

    def get_errors(self) -> list[ValidationIssue]:
        """Retrieve all validation issues with the ERROR severity level.

        Returns
        -------
        list[ValidationIssue]
            A list of ERROR-level validation issues.
        """
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """Retrieve all validation issues with the WARNING severity level.

        Returns
        -------
        list[ValidationIssue]
            A list of WARNING-level validation issues.
        """
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    def print_summary(self) -> None:
        """Print a formatted summary of the validation results, including errors and warnings.

        Notes
        -----
        If there are errors, they are displayed first. Warnings are displayed next.
        If no issues are found, a success message is printed.
        """
        if self.has_errors():
            logger.info('❌ Configuration invalid - Errors found:')
            for err in self.get_errors():
                _error = f'error:{err}'
                logger.info(_error)

        if self.has_warnings():
            logger.info('\n⚠️  Warnings:')
            for warning in self.get_warnings():
                _warning = f'{self.level.WARNING} {warning}'
                logger.info(_warning)

        if not self.has_errors() and not self.has_warnings():
            logger.info('✅ Configuration valid - No issues found')


# pylint: disable=too-few-public-methods
class ScenarioValidator:
    """Validate configurations for logical consistency and business rules.

    Checks:
    - Cross-field validation (capacity vs. arrival rate)
    - Business rules (at least 1 workshop track)
    - References (track IDs in routes exist)
    - Temporal consistency (trains within simulation time)
    """

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Perform all validations and return result.

        Parameters
        ----------
        scenario : Scenario
            Loaded scenario models.

        Returns
        -------
        ValidationResult
            Validation result with all found issues.
        """
        issues: list[ValidationIssue] = []

        # Perform all validations
        # TODO: verifiy validations
        issues.extend(self._validate_workshop_tracks(scenario))
        # TODO: clarify if needed
        # issues.extend(self._validate_capacity(scenario))
        issues.extend(self._validate_routes(scenario))
        # issues.extend(self._validate_train_schedule(scenario))
        # issues.extend(self._validate_simulation_duration(scenario))

        # is_valid = True when no errors
        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)

        return ValidationResult(is_valid=is_valid, issues=issues)

    def _validate_workshop_tracks(self, scenario: Scenario) -> list[ValidationIssue]:
        """Validate workshop tracks.

        Checks:
        - At least one workshop available
        - Workshop has tracks configured
        - Required track types available
        """
        issues: list[ValidationIssue] = []

        # Check if workshops are configured
        if not scenario.workshops:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message='No workshops configured',
                    field='workshops',
                    suggestion='Add at least one workshop with tracks',
                )
            )
            return issues

        # Validate first workshop
        workshop = scenario.workshops[0]

        if not scenario.tracks:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f'Workshop {workshop.workshop_id} has no tracks configured',
                    field='tracks',
                    suggestion='Add tracks to the workshop',
                )
            )
            return issues

        # 1. At least one workshop track
        werkstatt_tracks = [t for t in scenario.tracks if t.type == TrackType.WORKSHOP]

        if not werkstatt_tracks:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="At least one track with function='WORKSHOP' required",
                    field='tracks',
                    suggestion="Add a track with function='WORKSHOP'",
                )
            )

        # 2. All core tracktypes present?
        required_types = {TrackType.RETROFITTED, TrackType.WORKSHOP, TrackType.PARKING}
        present_types = {t.type for t in scenario.tracks}
        missing = required_types - present_types

        if missing:
            missing_names = [tracktype.value for tracktype in missing]
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f'Missing track type: {", ".join(missing_names)}',
                    field='tracks',
                    suggestion='Complete workflow needed: collection → WORKSHOP → parking',
                )
            )

        return issues

    def _validate_routes(self, scenario: Scenario) -> list[ValidationIssue]:
        """Validate routes.

        Checks:
        - Track IDs in track_sequence exist
        - from_function and to_function exist
        """
        issues: list[ValidationIssue] = []

        # Check if tracks are configured
        if not scenario.tracks:
            return issues  # Workshop validation already handles this case

        # Collect track IDs and function names
        track_ids = {t.id for t in scenario.tracks}
        function_names = {t.type.value for t in scenario.tracks}
        valid_identifiers = track_ids | function_names

        # Collect tracktypes
        tracktypes = {t.type for t in scenario.tracks}

        for route in scenario.routes or []:
            # Track IDs or function names exist?
            for track_identifier in route.track_sequence:
                if track_identifier not in valid_identifiers:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=f"Route {route.route_id}: Track '{track_identifier}' does not exist",
                            field=f'routes[{route.route_id}].track_sequence',
                            suggestion=f'Use one of the IDs: {", ".join(sorted(track_ids))}',
                        )
                    )

            # tracktypes exist?
            # Get the function of the from_track
            from_track = next((t for t in scenario.tracks if t.id == route.from_track), None)
            if from_track and from_track.type not in tracktypes:
                tracktype_names = [str(f) for f in tracktypes]
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Route {route.route_id}: from_track '{route.from_track}' "
                            f"has function '{from_track.type}' which does not exist"
                        ),
                        field=f'routes[{route.route_id}].from_track',
                        suggestion=f'Use one of the tracktypes: {", ".join(sorted(tracktype_names))}',
                    )
                )

            # Get the function of the to_track
            to_track = next((t for t in scenario.tracks if t.id == route.to_track), None)
            if to_track and to_track.type not in tracktypes:
                tracktype_names = [str(f) for f in tracktypes]
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Route {route.route_id}: to_track '{route.to_track}' "
                            f"has function '{to_track.type}' which does not exist"
                        ),
                        field=f'routes[{route.route_id}].to_track',
                        suggestion=f'Use one of the tracktypes: {", ".join(sorted(tracktype_names))}',
                    )
                )

        return issues

    def _validate_simulation_duration(self, scenario: Scenario) -> list[ValidationIssue]:
        """Validate whether all trains arrive within simulation time."""
        issues: list[ValidationIssue] = []

        sim_start = scenario.start_date
        sim_end = scenario.end_date

        if not sim_start or not sim_end:
            return issues

        for train in scenario.trains or []:
            arrival_date = train.arrival_time

            if arrival_date < sim_start:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f'Train {train.train_id} arrives before simulation start ({arrival_date})',
                        field=f'train[{train.train_id}].arrival_time',
                        suggestion='Adjust start_datetime or arrival_time',
                    )
                )

            if arrival_date > sim_end:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f'Train {train.train_id} arrives after simulation end ({arrival_date})',
                        field=f'train[{train.train_id}].arrival_time',
                        suggestion='Adjust stop_datetime or arrival_time',
                    )
                )

        return issues
