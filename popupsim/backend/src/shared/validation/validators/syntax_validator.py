"""Layer 1: Syntax validation - Basic field format and type checking."""

import re

from shared.validation.base import ValidationCategory
from shared.validation.base import ValidationResult

from configuration.domain.models.scenario import Scenario


class SyntaxValidator:  # pylint: disable=too-few-public-methods
    """Validates basic syntax: field presence, format, types."""

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate syntax layer."""
        result = ValidationResult(is_valid=True)

        # Basic field validation
        self._validate_required_fields(scenario, result)
        self._validate_field_formats(scenario, result)
        self._validate_collections(scenario, result)

        return result

    def _validate_required_fields(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate required fields are present."""
        if not scenario.id:
            result.add_error(
                'Scenario ID is required',
                field_name='id',
                category=ValidationCategory.SYNTAX,
                suggestion='Provide a unique scenario identifier',
            )

        if not scenario.start_date:
            result.add_error(
                'Start date is required',
                field_name='start_date',
                category=ValidationCategory.SYNTAX,
                suggestion='Provide simulation start date',
            )

        if not scenario.end_date:
            result.add_error(
                'End date is required',
                field_name='end_date',
                category=ValidationCategory.SYNTAX,
                suggestion='Provide simulation end date',
            )

    def _validate_field_formats(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate field formats and patterns."""
        if scenario.id and not re.match(r'^[a-zA-Z0-9_-]+$', scenario.id):
            result.add_error(
                'Scenario ID contains invalid characters',
                field_name='id',
                category=ValidationCategory.SYNTAX,
                suggestion='Use only letters, numbers, hyphens, and underscores',
            )

        if scenario.id and len(scenario.id) > 50:
            result.add_error(
                f'Scenario ID too long ({len(scenario.id)} chars)',
                field_name='id',
                category=ValidationCategory.SYNTAX,
                suggestion='Keep scenario ID under 50 characters',
            )

    def _validate_collections(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate collection fields are properly structured."""
        if scenario.trains is not None and not isinstance(scenario.trains, list):
            result.add_error(
                'Trains must be a list',
                field_name='trains',
                category=ValidationCategory.SYNTAX,
                suggestion='Ensure trains field is an array',
            )

        if scenario.workshops is not None and not isinstance(scenario.workshops, list):
            result.add_error(
                'Workshops must be a list',
                field_name='workshops',
                category=ValidationCategory.SYNTAX,
                suggestion='Ensure workshops field is an array',
            )
