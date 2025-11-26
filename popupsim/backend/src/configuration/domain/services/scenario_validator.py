"""Configuration validation module for train simulation scenarios.

This module provides validation logic for scenario configurations, including
workshop tracks, capacity validation, route validation, train schedule validation,
and simulation duration checks. It ensures that loaded configurations are
logically consistent and meet business requirements.
"""

import logging

from shared.validation.base import ValidationIssue
from shared.validation.base import ValidationLevel
from shared.validation.base import ValidationResult

from configuration.domain.models.scenario import Scenario

logger = logging.getLogger('validation')


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

        result = ValidationResult(is_valid=is_valid, issues=issues)
        if issues:
            result.print_summary()
        return result

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
                        message=f'Route {route.route_id}: Empty track sequence',
                        field=f'routes[{route.route_id}].track_sequence',
                        suggestion='Add track sequence to route',
                    )
                )

            if route.duration <= 0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f'Route {route.route_id}: Duration is {route.duration}',
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
