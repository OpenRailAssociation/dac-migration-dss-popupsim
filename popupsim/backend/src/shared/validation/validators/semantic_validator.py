"""Layer 2: Semantic validation - Business rules within entities."""

from shared.validation.base import ValidationCategory
from shared.validation.base import ValidationResult

from configuration.domain.models.scenario import Scenario


class SemanticValidator:  # pylint: disable=too-few-public-methods
    """Validates business rules and constraints within single entities."""

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate semantic layer."""
        result = ValidationResult(is_valid=True)

        self._validate_date_logic(scenario, result)
        self._validate_strategy_values(scenario, result)
        self._validate_entity_constraints(scenario, result)

        return result

    def _validate_date_logic(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate date ranges and business logic."""
        if scenario.start_date and scenario.end_date:
            if scenario.end_date <= scenario.start_date:
                result.add_error(
                    f'End date ({scenario.end_date}) must be after start date ({scenario.start_date})',
                    field_name='end_date',
                    category=ValidationCategory.SEMANTIC,
                    suggestion='Ensure simulation has positive duration',
                )

            duration = (scenario.end_date - scenario.start_date).days
            if duration > 365:
                result.add_warning(
                    f'Long simulation duration ({duration} days) may impact performance',
                    field_name='end_date',
                    category=ValidationCategory.SEMANTIC,
                    suggestion='Consider shorter simulation periods for better performance',
                )
            elif duration < 1:
                result.add_error(
                    f'Simulation duration too short ({duration} days)',
                    field_name='end_date',
                    category=ValidationCategory.SEMANTIC,
                    suggestion='Simulation must run for at least 1 day',
                )

    def _validate_strategy_values(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate strategy enum values."""
        valid_track_strategies = ['round_robin', 'least_occupied', 'first_available', 'random']
        valid_loco_strategies = ['return_to_parking', 'direct_delivery']

        if scenario.track_selection_strategy and str(scenario.track_selection_strategy) not in valid_track_strategies:
            result.add_error(
                f'Invalid track selection strategy: {scenario.track_selection_strategy}',
                field_name='track_selection_strategy',
                category=ValidationCategory.SEMANTIC,
                suggestion=f'Use one of: {", ".join(valid_track_strategies)}',
            )

        if scenario.loco_delivery_strategy and str(scenario.loco_delivery_strategy) not in valid_loco_strategies:
            result.add_error(
                f'Invalid locomotive delivery strategy: {scenario.loco_delivery_strategy}',
                field_name='loco_delivery_strategy',
                category=ValidationCategory.SEMANTIC,
                suggestion=f'Use one of: {", ".join(valid_loco_strategies)}',
            )

    def _validate_entity_constraints(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate constraints within individual entities."""
        # Validate workshops
        if scenario.workshops:
            for i, workshop in enumerate(scenario.workshops):
                if hasattr(workshop, 'retrofit_stations') and workshop.retrofit_stations <= 0:
                    result.add_error(
                        f'Workshop {workshop.id} has no retrofit stations',
                        field_name=f'workshops[{i}].retrofit_stations',
                        category=ValidationCategory.SEMANTIC,
                        suggestion='Set retrofit_stations > 0',
                    )

        # Validate routes
        if scenario.routes:
            for i, route in enumerate(scenario.routes):
                if hasattr(route, 'duration') and route.duration <= 0:
                    result.add_warning(
                        f'Route {route.id} has zero or negative duration',
                        field_name=f'routes[{i}].duration',
                        category=ValidationCategory.SEMANTIC,
                        suggestion='Set positive duration for realistic routing',
                    )
