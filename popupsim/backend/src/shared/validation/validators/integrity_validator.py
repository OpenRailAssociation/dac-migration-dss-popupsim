"""Layer 3: Integrity validation - Cross-reference and consistency checks."""

from datetime import datetime

from shared.validation.base import ValidationCategory
from shared.validation.base import ValidationResult

from configuration.domain.models.scenario import Scenario


class IntegrityValidator:  # pylint: disable=too-few-public-methods
    """Validates cross-references and data consistency across entities."""

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate integrity layer."""
        result = ValidationResult(is_valid=True)

        self._validate_cross_references(scenario, result)
        self._validate_data_consistency(scenario, result)
        self._validate_required_entities(scenario, result)

        return result

    def _validate_cross_references(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate ID references exist."""
        # Collect all available IDs
        locomotive_ids = {loco.id for loco in scenario.locomotives or []}
        route_ids = {route.id for route in scenario.routes or []}
        track_ids = {track.id for track in scenario.tracks or []}

        # Validate different types of references
        self._validate_train_references(scenario, result, locomotive_ids, route_ids)
        self._validate_workshop_references(scenario, result, track_ids)
        self._validate_route_references(scenario, result, track_ids)

    def _validate_train_references(
        self, scenario: Scenario, result: ValidationResult, locomotive_ids: set[str], route_ids: set[str]
    ) -> None:
        """Validate train references to locomotives and routes."""
        if not scenario.trains:
            return

        for i, train in enumerate(scenario.trains):
            # Check locomotive reference
            if hasattr(train, 'locomotive_id') and train.locomotive_id not in locomotive_ids:
                result.add_error(
                    f"Train {train.id} references non-existent locomotive '{train.locomotive_id}'",
                    field_name=f'trains[{i}].locomotive_id',
                    category=ValidationCategory.INTEGRITY,
                    suggestion=(
                        f'Use one of: {", ".join(locomotive_ids)}' if locomotive_ids else 'Add locomotives first'
                    ),
                )

            # Check route reference
            if hasattr(train, 'route_id') and train.route_id not in route_ids:
                result.add_error(
                    f"Train {train.id} references non-existent route '{train.route_id}'",
                    field_name=f'trains[{i}].route_id',
                    category=ValidationCategory.INTEGRITY,
                    suggestion=(f'Use one of: {", ".join(route_ids)}' if route_ids else 'Add routes first'),
                )

    def _validate_workshop_references(self, scenario: Scenario, result: ValidationResult, track_ids: set[str]) -> None:
        """Validate workshop references to tracks."""
        if not scenario.workshops:
            return

        for i, workshop in enumerate(scenario.workshops):
            if hasattr(workshop, 'track') and workshop.track not in track_ids:
                result.add_error(
                    f"Workshop {workshop.id} references non-existent track '{workshop.track}'",
                    field_name=f'workshops[{i}].track',
                    category=ValidationCategory.INTEGRITY,
                    suggestion=(f'Use one of: {", ".join(track_ids)}' if track_ids else 'Add tracks first'),
                )

    def _validate_route_references(self, scenario: Scenario, result: ValidationResult, track_ids: set[str]) -> None:
        """Validate route track sequence references."""
        if not scenario.routes:
            return

        for i, route in enumerate(scenario.routes):
            if hasattr(route, 'track_sequence'):
                for j, track_id in enumerate(route.track_sequence or []):
                    if track_id not in track_ids:
                        result.add_error(
                            f"Route {route.id} references non-existent track '{track_id}' in sequence",
                            field_name=f'routes[{i}].track_sequence[{j}]',
                            category=ValidationCategory.INTEGRITY,
                            suggestion=f'Use existing track ID from: {", ".join(track_ids)}',
                        )

    def _validate_data_consistency(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate data consistency across entities."""
        # Check for duplicate IDs
        self._check_duplicate_ids(scenario, result)

        # Validate time consistency
        self._validate_train_time_consistency(scenario, result)

    def _validate_train_time_consistency(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate train arrival/departure time consistency."""
        if not scenario.trains:
            return

        for i, train in enumerate(scenario.trains):
            if not (hasattr(train, 'arrival_time') and hasattr(train, 'departure_time')):
                continue
            try:
                arrival = datetime.fromisoformat(str(train.arrival_time))
                departure = datetime.fromisoformat(str(train.departure_time))

                if departure <= arrival:
                    result.add_error(
                        f'Train {train.id} departure time must be after arrival time',
                        field_name=f'trains[{i}].departure_time',
                        category=ValidationCategory.INTEGRITY,
                        suggestion='Ensure departure_time > arrival_time',
                    )
            except (ValueError, TypeError):
                result.add_error(
                    f'Train {train.id} has invalid time format',
                    field_name=f'trains[{i}].arrival_time',
                    category=ValidationCategory.INTEGRITY,
                    suggestion='Use ISO format: YYYY-MM-DDTHH:MM:SS',
                )

    def _check_duplicate_ids(self, scenario: Scenario, result: ValidationResult) -> None:
        """Check for duplicate IDs within collections."""
        # Check train IDs
        if scenario.trains:
            train_ids = [train.id for train in scenario.trains if hasattr(train, 'id')]
            duplicates = {x for x in train_ids if train_ids.count(x) > 1}
            for dup_id in duplicates:
                result.add_error(
                    f"Duplicate train ID: '{dup_id}'",
                    field_name='trains',
                    category=ValidationCategory.INTEGRITY,
                    suggestion='Ensure all train IDs are unique',
                )

        # Check workshop IDs
        if scenario.workshops:
            workshop_ids = [w.id for w in scenario.workshops if hasattr(w, 'id')]
            duplicates = {x for x in workshop_ids if workshop_ids.count(x) > 1}
            for dup_id in duplicates:
                result.add_error(
                    f"Duplicate workshop ID: '{dup_id}'",
                    field_name='workshops',
                    category=ValidationCategory.INTEGRITY,
                    suggestion='Ensure all workshop IDs are unique',
                )

    def _validate_required_entities(self, scenario: Scenario, result: ValidationResult) -> None:
        """Validate required entities are present for simulation."""
        if not scenario.locomotives:
            result.add_error(
                'No locomotives configured',
                field_name='locomotives',
                category=ValidationCategory.INTEGRITY,
                suggestion='Add at least one locomotive for wagon transport',
            )

        if not scenario.trains:
            result.add_error(
                'No trains configured',
                field_name='trains',
                category=ValidationCategory.INTEGRITY,
                suggestion='Add train schedule with wagons to process',
            )

        if not scenario.tracks:
            result.add_error(
                'No tracks configured',
                field_name='tracks',
                category=ValidationCategory.INTEGRITY,
                suggestion='Add track configuration for workshop operations',
            )
