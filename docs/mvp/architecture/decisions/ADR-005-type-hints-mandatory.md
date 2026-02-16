# ADR-005: Mandatory Type Hints with MyPy Strict Mode

## Status
**ACCEPTED** - Implemented January 2025

## Context

PopUpSim is a complex simulation system with multiple contexts, intricate domain models, and extensive validation logic. Type safety is critical for:

### Code Quality Requirements
- **Simulation Accuracy**: Type errors could lead to incorrect simulation results
- **Complex Domain Models**: Rich entities with multiple relationships need type safety
- **Validation Framework**: 4-layer validation requires precise type definitions
- **Cross-Context Integration**: Clear interfaces between bounded contexts
- **Maintainability**: Large codebase needs type-driven development

### Problems Without Type Hints
- **Runtime Errors**: Type mismatches discovered only during execution
- **Poor IDE Support**: Limited autocomplete and refactoring capabilities
- **Documentation Gaps**: Unclear function signatures and return types
- **Integration Issues**: Unclear interfaces between contexts
- **Maintenance Overhead**: Difficult to understand code without type information

## Decision

Implement **mandatory type hints** across the entire codebase with **MyPy strict mode** enforcement.

### Type Hint Requirements
- **All Functions**: Must have explicit return type annotations
- **All Methods**: Must have explicit return type annotations
- **All Parameters**: Must have type annotations
- **Complex Variables**: Must have type hints when type unclear
- **Generic Types**: Must use proper generic type annotations
- **Optional Types**: Must use `Optional` or union syntax explicitly

### MyPy Configuration
```toml
# pyproject.toml
[tool.mypy]
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_calls = true
warn_return_any = true
warn_unused_ignores = true
strict = true
```

### Enforcement Strategy
- **Pre-commit Hooks**: MyPy runs on every commit
- **CI/CD Pipeline**: Type checking in continuous integration
- **Development Workflow**: `uv run mypy backend/src/` in quality checks
- **Code Reviews**: Type hints required for all new code

## Alternatives Considered

### Alternative 1: Optional Type Hints
- **Pros**: Gradual adoption, less initial work
- **Cons**: Inconsistent type safety, partial benefits
- **Rejected**: Insufficient for complex simulation system

### Alternative 2: Runtime Type Checking (e.g., Pydantic everywhere)
- **Pros**: Runtime validation, automatic type checking
- **Cons**: Performance overhead, limited to data models
- **Rejected**: Not suitable for all code, performance impact

### Alternative 3: TypeScript-style Gradual Typing
- **Pros**: Flexible adoption
- **Cons**: Python's type system not as mature as TypeScript
- **Rejected**: Python type hints work differently than TypeScript

### Alternative 4: No Type Hints (Dynamic Python)
- **Pros**: Faster initial development
- **Cons**: Poor maintainability, runtime errors, unclear interfaces
- **Rejected**: Unacceptable for enterprise-grade simulation system

## Implementation

### Type Hint Examples

#### Functions and Methods
```python
def validate_scenario(scenario: Scenario) -> ValidationResult:
    """Validate scenario with explicit types."""
    return ValidationResult(is_valid=True)

def calculate_throughput(
    wagons: list[Wagon],
    duration: float
) -> ThroughputKPI:
    """Calculate throughput metrics."""
    return ThroughputKPI(wagons_per_hour=len(wagons) / duration)
```

#### Complex Generic Types
```python
from typing import Dict, List, Optional, Union, Generator
from pathlib import Path

def load_scenario_data(
    source: Path | str
) -> dict[str, list[dict[str, Any]]]:
    """Load scenario data with complex return type."""
    return {}

def process_wagons() -> Generator[Wagon, None, None]:
    """Generator with explicit type parameters."""
    yield Wagon(id="W1", track="T1")
```

#### Class Definitions
```python
class ValidationPipeline:
    """Pipeline with typed methods."""

    def __init__(self, validators: list[Validator]) -> None:
        self.validators = validators

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Validate with explicit return type."""
        result = ValidationResult(is_valid=True)
        return result
```

#### Domain Models with Pydantic
```python
from pydantic import BaseModel, Field
from typing import Optional

class Wagon(BaseModel):
    """Wagon entity with type-safe fields."""
    id: str = Field(min_length=1, max_length=50)
    track: str
    length: float = Field(gt=0)
    needs_retrofit: bool = True
    status: WagonStatus = WagonStatus.ARRIVED

    def update_status(self, new_status: WagonStatus) -> None:
        """Update status with type safety."""
        self.status = new_status
```

### Import Strategy
```python
# Standard typing imports
from typing import Any, Dict, List, Optional, Union, Generator
from typing_extensions import TypedDict, Literal  # For newer features
from pathlib import Path
from datetime import datetime
```

### Quality Assurance
```bash
# Development workflow
uv run ruff format .                    # Format code
uv run ruff check .                     # Lint code
uv run mypy backend/src/                # Type checking
uv run pylint backend/src/              # Code quality
uv run pytest                          # Run tests
```

## Consequences

### Positive
- **Type Safety**: Catch type errors at development time
- **Better IDE Support**: Excellent autocomplete, refactoring, navigation
- **Self-Documenting Code**: Function signatures clearly show expected types
- **Reduced Bugs**: Many runtime errors prevented by type checking
- **Better Refactoring**: Safe refactoring with type-aware tools
- **Team Productivity**: Clear interfaces reduce integration issues

### Negative
- **Initial Development Overhead**: More typing required upfront
- **Learning Curve**: Developers need to understand Python type system
- **Verbose Code**: Some type annotations can be lengthy
- **MyPy Complexity**: Advanced type features can be complex

### Migration Impact
- **Existing Code**: All functions updated with type hints
- **New Development**: Type hints mandatory from start
- **CI/CD**: MyPy integrated into quality checks
- **Documentation**: Type hints serve as inline documentation

## Validation

### Type Coverage Metrics
- **Functions**: 100% have return type annotations
- **Methods**: 100% have return type annotations
- **Parameters**: 100% have type annotations
- **MyPy Score**: 100% pass rate with strict mode

### Quality Improvements
- **IDE Experience**: Excellent autocomplete and error detection
- **Code Reviews**: Type information makes reviews more effective
- **Debugging**: Type errors caught before runtime
- **Documentation**: Self-documenting function signatures

### Examples of Prevented Errors
```python
# Type error caught by MyPy
def process_wagon(wagon: Wagon) -> None:
    wagon.update_status("COMPLETED")  # Error: expected WagonStatus, got str

# Correct usage
def process_wagon(wagon: Wagon) -> None:
    wagon.update_status(WagonStatus.COMPLETED)  # ✅ Type safe
```

## Compliance

This decision supports:
- **Code Quality**: Type safety prevents runtime errors
- **Maintainability**: Clear interfaces and self-documenting code
- **Team Productivity**: Better IDE support and refactoring capabilities
- **Simulation Accuracy**: Type safety critical for correct simulation results

## References

- Project Rules (see `.amazonq/rules/project-rules.md` in repository root)
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [MyPy Documentation](https://mypy.readthedocs.io/)

---

**Decision Date**: January 2025
**Decision Makers**: Architecture Team
**Implementation Status**: ✅ Complete