"""Base specification pattern implementation."""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class Specification[T](ABC):
    """Base specification for business rules."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies specification."""
        raise NotImplementedError

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Negate specification."""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """AND combination of specifications."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if both specifications are satisfied."""
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification[T]):
    """OR combination of specifications."""

    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if either specification is satisfied."""
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification[T]):
    """NOT negation of specification."""

    def __init__(self, spec: Specification[T]) -> None:
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if specification is not satisfied."""
        return not self.spec.is_satisfied_by(candidate)
