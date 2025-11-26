"""Domain-specific validation for workshop operations context."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from workshop_operations.domain.entities.track import TrackType
from configuration.domain.models.scenario import Scenario


class ValidationLevel(Enum):
    """Severity level of a validation message."""
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'


@dataclass
class DomainValidationIssue:
    """Domain validation issue."""
    level: ValidationLevel
    message: str
    field: str | None = None
    suggestion: str | None = None


@dataclass
class DomainValidationResult:
    """Result of domain validation."""
    is_valid: bool
    issues: list[DomainValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if there are any ERROR-level issues."""
        return any(i.level == ValidationLevel.ERROR for i in self.issues)


class ScenarioDomainValidator:
    """Domain-specific validator for workshop operations."""

    def validate_workshop_requirements(self, scenario: Scenario) -> DomainValidationResult:
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
                    message=f'Missing required track types: {", ".join(missing_names)}',
                    field='tracks',
                    suggestion='Complete workflow requires: collection → WORKSHOP → parking',
                )
            )

        return issues

    def _validate_workshop_capacity(self, scenario: Scenario) -> list[DomainValidationIssue]:
        """Validate workshop capacity requirements."""
        issues: list[DomainValidationIssue] = []

        if not scenario.workshops:
            return issues

        for workshop in scenario.workshops:
            if workshop.retrofit_stations <= 0:
                issues.append(
                    DomainValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f'Workshop {workshop.workshop_id} has no retrofit stations',
                        field=f'workshops[{workshop.workshop_id}].retrofit_stations',
                        suggestion='Set retrofit_stations > 0',
                    )
                )

        return issues