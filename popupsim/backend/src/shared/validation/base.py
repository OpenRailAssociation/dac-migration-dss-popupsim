"""Base validation components shared across contexts."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
import logging

logger = logging.getLogger('validation')


class ValidationLevel(Enum):
    """Severity level of a validation message."""

    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'


class ValidationCategory(Enum):
    """Validation layer category."""

    SYNTAX = 'SYNTAX'
    SEMANTIC = 'SEMANTIC'
    INTEGRITY = 'INTEGRITY'
    FEASIBILITY = 'FEASIBILITY'


@dataclass
class ValidationIssue:
    """Validation issue with severity level."""

    level: ValidationLevel
    message: str
    category: ValidationCategory | None = None
    component: str | None = None
    field: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return formatted string representation."""
        category_str = f'{self.category.value}: ' if self.category else ''
        result = f'[{self.level.value}] {category_str}{self.message}'
        if self.field:
            result += f' (Field: {self.field})'
        if self.suggestion:
            result += f'\n  → Suggestion: {self.suggestion}'
        return result


@dataclass
class ValidationResult:
    """Result of validation process."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if there are any ERROR-level issues."""
        return any(i.level == ValidationLevel.ERROR for i in self.issues)

    def get_errors(self) -> list[ValidationIssue]:
        """Get only ERROR-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """Get only WARNING-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    def has_warnings(self) -> bool:
        """Check if there are any WARNING-level issues."""
        return any(i.level == ValidationLevel.WARNING for i in self.issues)

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        # Keep is_valid as False if either result has errors
        if other.has_errors():
            self.is_valid = False

    def add_error(
        self,
        message: str,
        field_name: str | None = None,
        category: ValidationCategory | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error to the validation result."""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR,
                message=message,
                field=field_name,
                category=category,
                suggestion=suggestion,
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        message: str,
        field_name: str | None = None,
        category: ValidationCategory | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add a warning to the validation result."""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message=message,
                field=field_name,
                category=category,
                suggestion=suggestion,
            )
        )

    def get_issues_by_category(self, category: ValidationCategory) -> list[ValidationIssue]:
        """Get issues filtered by category."""
        return [i for i in self.issues if i.category == category]

    def print_summary(self) -> None:
        """Print formatted summary of validation results grouped by category."""
        if not self.issues:
            logger.info('✅ Configuration valid - No issues found')
            return

        logger.info(
            '📋 Validation Summary: %d errors, %d warnings',
            len(self.get_errors()),
            len(self.get_warnings()),
        )

        # Group by category
        for category in ValidationCategory:
            category_issues = self.get_issues_by_category(category)
            if category_issues:
                logger.info('\n%s ISSUES:', category.value)
                for issue in category_issues:
                    logger.info('  %s', issue)
