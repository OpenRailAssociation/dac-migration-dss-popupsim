"""Domain-specific validation for workshop operations context."""

from MVP.configuration.domain.models.scenario import Scenario
from MVP.workshop_operations.domain.entities.track import TrackType
from shared.validation.base import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)

# Type aliases for domain-specific validation
DomainValidationIssue = ValidationIssue
DomainValidationResult = ValidationResult


class ScenarioDomainValidator:
    """Domain-specific validator for workshop operations."""

    def validate_workshop_requirements(
        self, scenario: Scenario
    ) -> DomainValidationResult:
        """Validate workshop-specific domain requirements."""
        issues: list[DomainValidationIssue] = []

        # Domain-specific track validation
        issues.extend(self._validate_track_types(scenario))
        issues.extend(self._validate_workshop_capacity(scenario))

        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)
        return DomainValidationResult(is_valid=is_valid, issues=issues)

    def _validate_track_types(self, scenario: Scenario) -> list[DomainValidationIssue]:
        """Validate required track types for workshop operations."""
        issues: list[DomainValidationIssue] = []

        if not scenario.tracks:
            return issues

        # Check for required track types
        required_types = {TrackType.RETROFITTED, TrackType.WORKSHOP, TrackType.PARKING}
        present_types = {t.type for t in scenario.tracks}
        missing = required_types - present_types

        if missing:
            missing_names = [tracktype.value for tracktype in missing]
            issues.append(
                DomainValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Missing required track types: {', '.join(missing_names)}",
                    field="tracks",
                    suggestion="Complete workflow requires: collection → WORKSHOP → parking",
                )
            )

        return issues

    def _validate_workshop_capacity(
        self, scenario: Scenario
    ) -> list[DomainValidationIssue]:
        """Validate workshop capacity requirements."""
        issues: list[DomainValidationIssue] = []

        if not scenario.workshops:
            return issues

        for workshop in scenario.workshops:
            if workshop.retrofit_stations <= 0:
                issues.append(
                    DomainValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Workshop {workshop.id} has no retrofit stations",
                        field=f"workshops[{workshop.id}].retrofit_stations",
                        suggestion="Set retrofit_stations > 0",
                    )
                )

        return issues

    def validate_locomotive_requirements(
        self, scenario: Scenario
    ) -> DomainValidationResult:
        """Validate locomotive configuration requirements."""
        issues: list[DomainValidationIssue] = []

        if not scenario.locomotives:
            issues.append(
                DomainValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="No locomotives configured - simulation may not function properly",
                    field="locomotives",
                    suggestion="Add at least one locomotive for wagon transport",
                )
            )

        is_valid = not any(i.level == ValidationLevel.ERROR for i in issues)
        return DomainValidationResult(is_valid=is_valid, issues=issues)
