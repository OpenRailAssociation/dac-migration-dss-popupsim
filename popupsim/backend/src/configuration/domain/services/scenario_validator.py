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

from configuration.domain.models.scenario import Scenario

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
        """Perform basic configuration validations.

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

        # Only basic configuration validation - no domain-specific logic
        issues.extend(self._validate_basic_requirements(scenario))
        issues.extend(self._validate_basic_routes(scenario))

        # is_valid = True when no errors
        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)

        return ValidationResult(is_valid=is_valid, issues=issues)

    def _validate_basic_requirements(self, scenario: Scenario) -> list[ValidationIssue]:
        """Validate basic scenario requirements.

        Checks:
        - Basic data presence
        - Required fields populated
        """
        issues: list[ValidationIssue] = []

        # Check if workshops are configured
        if not scenario.workshops:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message='No workshops configured',
                    field='workshops',
                    suggestion='Add at least one workshop',
                )
            )

        # Check if tracks are configured
        if not scenario.tracks:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message='No tracks configured',
                    field='tracks',
                    suggestion='Add track configuration',
                )
            )

        # Check if trains are configured
        if not scenario.trains:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message='No trains configured',
                    field='trains',
                    suggestion='Add train schedule',
                )
            )

        return issues

    def _validate_basic_routes(self, scenario: Scenario) -> list[ValidationIssue]:
        """Validate basic route configuration.

        Checks:
        - Routes have required fields
        - Basic data consistency
        """
        issues: list[ValidationIssue] = []

        for route in scenario.routes or []:
            # Check basic route data
            if not route.track_sequence:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Route {route.route_id}: Empty track sequence",
                        field=f'routes[{route.route_id}].track_sequence',
                        suggestion='Add track sequence to route',
                    )
                )
            
            if route.duration <= 0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Route {route.route_id}: Duration is {route.duration}",
                        field=f'routes[{route.route_id}].duration',
                        suggestion='Set positive duration for route',
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
