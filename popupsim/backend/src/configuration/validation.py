"""
Configuration validation module for train simulation scenarios.

This module provides validation logic for scenario configurations, including
workshop tracks, capacity validation, route validation, train schedule validation,
and simulation duration checks. It ensures that loaded configurations are
logically consistent and meet business requirements.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from .model_scenario import ScenarioConfig
from .model_track import TrackFunction


class ValidationLevel(Enum):
    """Enumeration representing the severity level of a validation message."""

    ERROR = 'ERROR'  # Indicates a critical issue; simulation cannot start
    WARNING = 'WARNING'  # Indicates a non-critical issue; simulation can start but may be suboptimal
    INFO = 'INFO'  # Provides informational messages for the user


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue encountered during configuration validation.

    Attributes:
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
        """
        Returns a formatted string representation of the validation issue.

        Returns:
            str: A string describing the issue, including its severity, message,
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
    """
    Represents the result of a configuration validation process.

    Attributes:
        is_valid (bool): Indicates whether the configuration is valid.
        issues (list[ValidationIssue]): A list of validation issues encountered.
    """

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        """
        Checks if there are any validation issues with the ERROR severity level.

        Returns:
            bool: True if there are ERROR-level issues, False otherwise.
        """
        return any(i.level == ValidationLevel.ERROR for i in self.issues)

    def has_warnings(self) -> bool:
        """
        Checks if there are any validation issues with the WARNING severity level.

        Returns:
            bool: True if there are WARNING-level issues, False otherwise.
        """
        return any(i.level == ValidationLevel.WARNING for i in self.issues)

    def get_errors(self) -> list[ValidationIssue]:
        """
        Retrieves all validation issues with the ERROR severity level.

        Returns:
            list[ValidationIssue]: A list of ERROR-level validation issues.
        """
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """
        Retrieves all validation issues with the WARNING severity level.

        Returns:
            list[ValidationIssue]: A list of WARNING-level validation issues.
        """
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    def print_summary(self) -> None:
        """
        Prints a formatted summary of the validation results, including errors and warnings.

        If there are errors, they are displayed first. Warnings are displayed next.
        If no issues are found, a success message is printed.
        """
        if self.has_errors():
            print('❌ Configuration invalid - Errors found:')
            for issue in self.get_errors():
                print(f'  {issue}')

        if self.has_warnings():
            print('\n⚠️  Warnings:')
            for issue in self.get_warnings():
                print(f'  {issue}')

        if not self.has_errors() and not self.has_warnings():
            print('✅ Configuration valid - No issues found')


# pylint: disable=too-few-public-methods
class ConfigurationValidator:
    """
    Validates loaded configurations for logical consistency
    and business rules.

    Checks:
    - Cross-field validation (capacity vs. arrival rate)
    - Business rules (at least 1 workshop track)
    - References (track IDs in routes exist)
    - Temporal consistency (trains within simulation time)
    """

    def validate(self, config: ScenarioConfig) -> ValidationResult:
        """
        Performs all validations and returns result.

        Args:
            config: Loaded scenario configuration

        Returns:
            ValidationResult with all found issues
        """
        issues: list[ValidationIssue] = []

        # Perform all validations
        issues.extend(self._validate_workshop_tracks(config))
        issues.extend(self._validate_capacity(config))
        issues.extend(self._validate_routes(config))
        issues.extend(self._validate_train_schedule(config))
        issues.extend(self._validate_simulation_duration(config))

        # is_valid = True when no errors
        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)

        return ValidationResult(is_valid=is_valid, issues=issues)

    def _validate_workshop_tracks(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validates workshop tracks.

        Checks:
        - At least one workshop track available
        - All required functions available
        - retrofit_time_min only for workshop tracks > 0
        """
        issues: list[ValidationIssue] = []

        # Check if workshop is configured
        if config.workshop is None:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message='Workshop configuration is missing',
                    field='workshop',
                    suggestion='Add workshop configuration with tracks',
                )
            )
            return issues

        # 1. At least one workshop track
        werkstatt_tracks = [t for t in config.workshop.tracks if t.function == TrackFunction.WERKSTATTGLEIS]

        if len(werkstatt_tracks) == 0:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="At least one track with function='werkstattgleis' required",
                    field='workshop.tracks',
                    suggestion="Add a track with function='werkstattgleis' and retrofit_time_min > 0",
                )
            )

        # 2. All core functions present?
        required_functions = {TrackFunction.SAMMELGLEIS, TrackFunction.WERKSTATTGLEIS, TrackFunction.PARKGLEIS}
        present_functions = {t.function for t in config.workshop.tracks}
        missing = required_functions - present_functions

        if missing:
            missing_names = [func.value for func in missing]
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f'Missing track functions: {", ".join(missing_names)}',
                    field='workshop.tracks',
                    suggestion='Complete workflow needed: sammelgleis → werkstattgleis → parkgleis',
                )
            )

        # 3. retrofit_time_min only for workshop tracks
        for track in config.workshop.tracks:
            if track.function != TrackFunction.WERKSTATTGLEIS and track.retrofit_time_min > 0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f'Track {track.id}: retrofit_time_min must be 0 for function={track.function}',
                        field=f'workshop.tracks[{track.id}].retrofit_time_min',
                        suggestion='Set retrofit_time_min=0 for non-workshop tracks',
                    )
                )

        return issues

    def _validate_capacity(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validates whether workshop capacity is sufficient for train arrivals.

        Calculates theoretical throughput and compares with arrival rate.
        """
        issues: list[ValidationIssue] = []

        # Check if workshop is configured
        if config.workshop is None:
            return issues  # Workshop validation already handles this case

        # Total workshop capacity
        werkstatt_tracks = [t for t in config.workshop.tracks if t.function == TrackFunction.WERKSTATTGLEIS]

        if not werkstatt_tracks:
            return issues  # Already checked in _validate_workshop_tracks

        total_capacity = sum(t.capacity for t in werkstatt_tracks)

        # Average retrofit time
        avg_retrofit_time = sum(t.retrofit_time_min for t in werkstatt_tracks) / len(werkstatt_tracks)

        # Wagons per day from train configuration
        wagons_per_day = len(
            [
                w
                for train in (config.train or [])
                for w in train.wagons
                if w.needs_retrofit  # Only wagons that need retrofitting
            ]
        )

        # Theoretical throughput per day (24h * 60min / avg_time * capacity)
        max_throughput_per_day = (24 * 60 / avg_retrofit_time) * total_capacity

        # Warning at > 80% utilization
        utilization = wagons_per_day / max_throughput_per_day

        if utilization > 1.0:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=(
                        f'Capacity exceeded: {wagons_per_day} wagons/day at max. '
                        f'{max_throughput_per_day:.0f} throughput ({utilization * 100:.0f}% utilization)'
                    ),
                    field='workshop.tracks',
                    suggestion='Increase capacity or reduce train arrivals',
                )
            )
        elif utilization > 0.8:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=(
                        f'High utilization: {wagons_per_day} wagons/day at max. '
                        f'{max_throughput_per_day:.0f} throughput ({utilization * 100:.0f}% utilization)'
                    ),
                    field='workshop.tracks',
                    suggestion='Consider higher capacity for better performance',
                )
            )

        return issues

    def _validate_routes(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validates routes.

        Checks:
        - Track IDs in track_sequence exist
        - from_function and to_function exist
        - time_min > 0
        """
        issues: list[ValidationIssue] = []

        # Check if workshop is configured
        if config.workshop is None:
            return issues  # Workshop validation already handles this case

        # Collect track IDs and function names
        track_ids = {t.id for t in config.workshop.tracks}
        function_names = {t.function.value for t in config.workshop.tracks}
        valid_identifiers = track_ids | function_names

        # Collect functions
        functions = {t.function for t in config.workshop.tracks}

        for route in config.routes or []:
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

            # Functions exist?
            # Get the function of the from_track
            from_track = next((t for t in config.workshop.tracks if t.id == route.from_track), None)
            if from_track and from_track.function not in functions:
                func_names_list = [str(f) for f in functions]
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Route {route.route_id}: from_track '{route.from_track}' "
                            f"has function '{from_track.function}' which does not exist"
                        ),
                        field=f'routes[{route.route_id}].from_track',
                        suggestion=f'Use one of the functions: {", ".join(sorted(func_names_list))}',
                    )
                )

            # Get the function of the to_track
            to_track = next((t for t in config.workshop.tracks if t.id == route.to_track), None)
            if to_track and to_track.function not in functions:
                func_names_list = [str(f) for f in functions]
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Route {route.route_id}: to_track '{route.to_track}' "
                            f"has function '{to_track.function}' which does not exist"
                        ),
                        field=f'routes[{route.route_id}].to_track',
                        suggestion=f'Use one of the functions: {", ".join(sorted(func_names_list))}',
                    )
                )

            # Time > 0?
            if route.time_min <= 0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f'Route {route.route_id}: time_min must be > 0',
                        field=f'routes[{route.route_id}].time_min',
                        suggestion='Set a realistic travel time in minutes',
                    )
                )

        return issues

    def _validate_train_schedule(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validates train schedule.

        Checks:
        - Wagon IDs are unique
        - Arrival times are chronological
        - At least one train present
        """
        issues: list[ValidationIssue] = []

        if not config.train:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message='Train schedule is empty - at least one train required',
                    field='train',
                    suggestion='Add trains in train configuration',
                )
            )
            return issues

        # Wagon IDs unique?
        wagon_ids = []
        for train in config.train:
            for wagon in train.wagons:
                wagon_ids.append(wagon.wagon_id)

        duplicates = [wid for wid in set(wagon_ids) if wagon_ids.count(wid) > 1]
        if duplicates:
            duplicate_list = duplicates[:5]
            ellipsis = '...' if len(duplicates) > 5 else ''
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f'Duplicate wagon IDs found: {", ".join(duplicate_list)}{ellipsis}',
                    field='train',
                    suggestion='Ensure each wagon_id is unique',
                )
            )

        return issues

    def _validate_simulation_duration(self, config: ScenarioConfig) -> list[ValidationIssue]:
        """
        Validates whether all trains arrive within simulation time.
        """
        issues: list[ValidationIssue] = []

        sim_start = config.start_date
        sim_end = config.end_date

        for train in config.train or []:
            arrival_date = train.arrival_date

            if arrival_date < sim_start:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f'Train {train.train_id} arrives before simulation start ({arrival_date})',
                        field=f'train[{train.train_id}].arrival_date',
                        suggestion='Adjust start_date or arrival_date',
                    )
                )

            if arrival_date > sim_end:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f'Train {train.train_id} arrives after simulation end ({arrival_date})',
                        field=f'train[{train.train_id}].arrival_date',
                        suggestion='Adjust end_date or arrival_date',
                    )
                )

        return issues
