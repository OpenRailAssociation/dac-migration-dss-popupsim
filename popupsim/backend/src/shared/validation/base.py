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


@dataclass
class ValidationIssue:
    """Validation issue with severity level."""

    level: ValidationLevel
    message: str
    component: str | None = None
    field: str | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return formatted string representation."""
        result = f'[{self.level.value}] {self.message}'
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

    def print_summary(self) -> None:
        """Print formatted summary of validation results."""
        if self.has_errors():
            logger.info('❌ Configuration invalid - Errors found:')
            for err in self.get_errors():
                logger.info('error:%s', err)

        if self.has_warnings():
            logger.info('\n⚠️  Warnings:')
            for warning in self.get_warnings():
                logger.info('WARNING %s', warning)

        if not self.has_errors() and not self.has_warnings():
            logger.info('✅ Configuration valid - No issues found')
