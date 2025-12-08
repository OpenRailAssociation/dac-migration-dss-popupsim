"""Layer 4: Feasibility validation - Operational constraints and simulation readiness."""

from datetime import datetime

from MVP.configuration.domain.models.scenario import Scenario
from shared.validation.base import (
    ValidationCategory,
    ValidationResult,
)


class FeasibilityValidator:  # pylint: disable=too-few-public-methods
    """Validates operational feasibility and simulation readiness."""

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate feasibility layer."""
        result = ValidationResult(is_valid=True)

        self._validate_capacity_constraints(scenario, result)
        self._validate_operational_feasibility(scenario, result)
        self._validate_simulation_readiness(scenario, result)

        return result

    def _validate_capacity_constraints(
        self, scenario: Scenario, result: ValidationResult
    ) -> None:
        """Validate capacity vs demand constraints."""
        if not scenario.workshops or not scenario.trains:
            return

        # Calculate total workshop capacity
        total_retrofit_capacity = sum(
            getattr(w, "retrofit_stations", 0) for w in scenario.workshops
        )

        # Calculate total wagons needing retrofit
        total_wagons = 0
        for train in scenario.trains:
            if hasattr(train, "wagons"):
                total_wagons += len(train.wagons or [])

        if total_retrofit_capacity == 0:
            result.add_error(
                "No retrofit capacity available",
                field_name="workshops",
                category=ValidationCategory.FEASIBILITY,
                suggestion="Add workshops with retrofit_stations > 0",
            )
        elif total_wagons > 0:
            # Simple capacity check (could be more sophisticated)
            capacity_ratio = total_wagons / total_retrofit_capacity
            if capacity_ratio > 100:  # More than 100 wagons per station
                result.add_warning(
                    f"High wagon-to-station ratio ({capacity_ratio:.1f}:1) may cause bottlenecks",
                    field_name="workshops",
                    category=ValidationCategory.FEASIBILITY,
                    suggestion="Consider adding more retrofit stations or reducing wagon count",
                )

    def _validate_operational_feasibility(
        self, scenario: Scenario, result: ValidationResult
    ) -> None:
        """Validate operational constraints."""
        # Check locomotive availability vs train count
        if scenario.locomotives and scenario.trains:
            loco_count = len(scenario.locomotives)
            train_count = len(scenario.trains)

            if loco_count < train_count:
                result.add_warning(
                    f"Fewer locomotives ({loco_count}) than trains ({train_count})",
                    field_name="locomotives",
                    category=ValidationCategory.FEASIBILITY,
                    suggestion="Add more locomotives or schedule trains sequentially",
                )

        # Validate track types for complete workflow
        if scenario.tracks:
            track_types = {getattr(t, "type", None) for t in scenario.tracks}
            required_types = {"WORKSHOP", "PARKING"}  # Simplified check

            missing_types = required_types - {str(t) for t in track_types if t}
            if missing_types:
                result.add_warning(
                    f"Missing track types for complete workflow: {', '.join(missing_types)}",
                    field_name="tracks",
                    category=ValidationCategory.FEASIBILITY,
                    suggestion="Add tracks for complete collection → workshop → parking workflow",
                )

    def _validate_simulation_readiness(
        self, scenario: Scenario, result: ValidationResult
    ) -> None:
        """Validate scenario is ready for simulation execution."""
        # Check if all trains arrive within simulation window
        if scenario.trains and scenario.start_date and scenario.end_date:
            for i, train in enumerate(scenario.trains):
                if hasattr(train, "arrival_time"):
                    try:
                        arrival = datetime.fromisoformat(str(train.arrival_time))

                        if arrival < scenario.start_date:
                            result.add_warning(
                                f"Train {train.id} arrives before simulation start",
                                field_name=f"trains[{i}].arrival_time",
                                category=ValidationCategory.FEASIBILITY,
                                suggestion="Adjust simulation start_date or train arrival_time",
                            )
                        elif arrival > scenario.end_date:
                            result.add_warning(
                                f"Train {train.id} arrives after simulation end",
                                field_name=f"trains[{i}].arrival_time",
                                category=ValidationCategory.FEASIBILITY,
                                suggestion="Extend simulation end_date or adjust train arrival_time",
                            )
                    except (ValueError, TypeError):
                        # Already caught in integrity layer
                        pass

        # Check process times configuration
        if not scenario.process_times:
            result.add_warning(
                "No process times configured - using defaults",
                field_name="process_times",
                category=ValidationCategory.FEASIBILITY,
                suggestion="Configure process_times for realistic simulation timing",
            )

        # Check topology configuration
        if not scenario.topology:
            result.add_warning(
                "No topology configured",
                field_name="topology",
                category=ValidationCategory.FEASIBILITY,
                suggestion="Configure topology for realistic track connections",
            )
