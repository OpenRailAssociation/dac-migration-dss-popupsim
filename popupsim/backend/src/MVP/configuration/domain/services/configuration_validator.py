"""Configuration context validator."""

import re
from datetime import datetime

from MVP.configuration.domain.models.scenario import Scenario
from shared.validation.base import ValidationResult


class ConfigurationValidator:  # pylint: disable=too-few-public-methods
    """Validates configuration context concerns."""

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate all configuration concerns."""
        result = ValidationResult(is_valid=True)

        # Basic data validation
        result.merge(self._validate_scenario_basic(scenario))
        result.merge(self._validate_dates(scenario))
        result.merge(self._validate_ids(scenario))
        result.merge(self._validate_strategies(scenario))
        result.merge(self._validate_required_data(scenario))

        return result

    def _validate_scenario_basic(self, scenario: Scenario) -> ValidationResult:
        """Validate basic scenario fields."""
        result = ValidationResult(is_valid=True)

        if not scenario.id or not scenario.id.strip():
            result.add_error("Scenario ID is required", "id")
        elif not re.match(r"^[a-zA-Z0-9_-]+$", scenario.id):
            result.add_error(
                "Scenario ID must contain only letters, numbers, hyphens, and underscores",
                "id",
            )
        elif len(scenario.id) > 50:
            result.add_error("Scenario ID must be 50 characters or less", "id")

        return result

    def _validate_dates(self, scenario: Scenario) -> ValidationResult:
        """Validate date fields and ranges."""
        result = ValidationResult(is_valid=True)

        if not scenario.start_date:
            result.add_error("Start date is required", "start_date")
            return result

        if not scenario.end_date:
            result.add_error("End date is required", "end_date")
            return result

        if scenario.end_date <= scenario.start_date:
            result.add_error(
                f"End date ({scenario.end_date}) must be after start date ({scenario.start_date})",
                "end_date",
            )

        duration = (scenario.end_date - scenario.start_date).days
        if duration > 365:
            result.add_warning(
                f"Simulation duration of {duration} days may impact performance",
                "end_date",
            )

        return result

    def _validate_ids(self, scenario: Scenario) -> ValidationResult:
        """Validate ID fields in trains and other entities."""
        result = ValidationResult(is_valid=True)

        if scenario.trains:
            for i, train in enumerate(scenario.trains):
                if hasattr(train, "id"):
                    if not train.id or not train.id.strip():
                        result.add_error(f"Train {i} ID is required", f"trains[{i}].id")
                    elif not re.match(r"^[a-zA-Z0-9_-]+$", train.id):
                        result.add_error(
                            f"Train {train.id} ID must contain only letters, numbers, hyphens, and underscores",
                            f"trains[{i}].id",
                        )

                # Validate train times
                if hasattr(train, "arrival_time") and hasattr(train, "departure_time"):
                    try:
                        arrival = datetime.fromisoformat(str(train.arrival_time))
                        departure = datetime.fromisoformat(str(train.departure_time))
                        if departure <= arrival:
                            result.add_error(
                                f"Train {train.id} departure time must be after arrival time",
                                f"trains[{i}].departure_time",
                            )
                    except (ValueError, TypeError):
                        result.add_error(
                            f"Train {train.id} has invalid time format",
                            f"trains[{i}].arrival_time",
                        )

        return result

    def _validate_strategies(self, scenario: Scenario) -> ValidationResult:
        """Validate strategy enum values."""
        result = ValidationResult(is_valid=True)
        # pylint: disable=duplicate-code
        valid_track_strategies = [
            "round_robin",
            "least_occupied",
            "first_available",
            "random",
        ]
        valid_loco_strategies = ["return_to_parking", "direct_delivery"]

        if (
            hasattr(scenario, "track_selection_strategy")
            and scenario.track_selection_strategy
            and str(scenario.track_selection_strategy) not in valid_track_strategies
        ):
            result.add_error(
                f"Invalid track selection strategy: {scenario.track_selection_strategy}. "
                f"Must be one of: {', '.join(valid_track_strategies)}",
                "track_selection_strategy",
            )

        if (
            hasattr(scenario, "loco_delivery_strategy")
            and scenario.loco_delivery_strategy
            and str(scenario.loco_delivery_strategy) not in valid_loco_strategies
        ):
            result.add_error(
                f"Invalid locomotive delivery strategy: {scenario.loco_delivery_strategy}. "
                f"Must be one of: {', '.join(valid_loco_strategies)}",
                "loco_delivery_strategy",
            )

        return result

    def _validate_required_data(self, scenario: Scenario) -> ValidationResult:
        """Validate required data is present."""
        result = ValidationResult(is_valid=True)

        if not scenario.locomotives:
            result.add_error(
                "Scenario must have at least one locomotive", "locomotives"
            )

        if not scenario.trains:
            result.add_error("Scenario must have at least one train", "trains")

        if not scenario.tracks:
            result.add_error("Scenario must have tracks defined", "tracks")

        if not scenario.topology:
            result.add_error("Scenario must have topology defined", "topology")

        return result
