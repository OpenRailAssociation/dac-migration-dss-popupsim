# ADR-008: Pydantic for Data Validation

**Status:** Accepted - 2025-01-15

## Context

Need robust input validation for JSON/CSV configuration files with clear error messages.

## Decision

Use **Pydantic** for data validation and parsing.

## Rationale

- **Type safety**: Excellent integration with Python type hints (matches project rules)
- **Validation**: Automatic validation with clear error messages
- **Performance**: Fast (Rust-based core in Pydantic v2)
- **JSON Schema**: Can generate schemas for documentation
- **IDE support**: Great autocomplete and type checking
- **Standard**: De facto standard in modern Python projects

## Alternatives Considered

- **Pydantic** ✅ Chosen
- **dataclasses**: No validation capabilities
- **attrs**: Less popular, fewer features
- **marshmallow**: Older, slower, less type-safe
- **cerberus**: Less Pythonic, no type hints

## Consequences

- **Positive**: Type-safe code, excellent validation, good error messages
- **Negative**: Additional dependency (minimal concern)
- **Benefit**: Enforces project's type hint requirements