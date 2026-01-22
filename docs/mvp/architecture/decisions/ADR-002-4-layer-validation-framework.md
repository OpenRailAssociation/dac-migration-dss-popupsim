# ADR-002: 4-Layer Validation Framework with Error Stacking

## Status
**ACCEPTED** - Implemented January 2025

## Context

PopUpSim requires comprehensive validation of complex scenario configurations with multiple interdependent entities (trains, wagons, workshops, locomotives, routes, tracks). Traditional fail-fast validation approaches create poor user experience by requiring multiple validation cycles to identify all issues.

### Problems with Traditional Validation
- **Poor UX**: Users must fix one error at a time, run validation again, discover next error
- **Development Inefficiency**: Multiple validation cycles slow down configuration development
- **Limited Context**: Single error messages provide insufficient information for complex fixes
- **Inconsistent Validation**: Different validation rules scattered across codebase without coordination

### Requirements
- Validate complex cross-references between entities
- Provide comprehensive error reporting in single validation run
- Categorize validation issues by type and severity
- Support enterprise-grade error messages with actionable suggestions
- Enable extensible validation framework for future requirements

## Decision

Implement a **4-Layer Validation Pipeline** with comprehensive **Error Stacking** instead of traditional fail-fast validation.

### Architecture Decision

```
Layer 1: SYNTAX     → Field format, types, required fields
Layer 2: SEMANTIC   → Business rules within entities  
Layer 3: INTEGRITY  → Cross-references, data consistency
Layer 4: FEASIBILITY → Operational constraints, simulation readiness
```

### Key Components
- **ValidationPipeline**: Orchestrates all 4 validation layers
- **ValidationResult**: Collects and categorizes all issues (no fail-fast)
- **ValidationCategory**: Enum for layer categorization (SYNTAX, SEMANTIC, INTEGRITY, FEASIBILITY)
- **ValidationCoordinator**: Cross-context validation coordination
- **Layer-Specific Validators**: Focused validators for each validation concern

### Error Stacking Strategy
- **Collect ALL Issues**: Run all validation layers regardless of errors found
- **Categorize by Layer**: Group issues by validation layer for clarity
- **Actionable Suggestions**: Each error includes specific fix recommendation
- **Professional Reporting**: Enterprise-grade error summaries with issue counts

## Alternatives Considered

### Alternative 1: Fail-Fast Validation (Traditional)
- **Pros**: Simple implementation, fast failure on first error
- **Cons**: Poor user experience, multiple validation cycles required, limited error context
- **Rejected**: Inadequate for complex scenario validation requirements

### Alternative 2: Pydantic-Only Validation
- **Pros**: Built-in validation, type safety
- **Cons**: Limited to field-level validation, no cross-reference validation, poor error categorization
- **Rejected**: Insufficient for complex business rule validation

### Alternative 3: Single-Layer Comprehensive Validation
- **Pros**: All validation in one place
- **Cons**: Monolithic validator, difficult to maintain, poor separation of concerns
- **Rejected**: Not scalable or maintainable for complex validation requirements

### Alternative 4: Event-Driven Validation
- **Pros**: Flexible, extensible
- **Cons**: Complex implementation, difficult to coordinate, potential performance issues
- **Rejected**: Over-engineered for current requirements

## Implementation

### Core Framework
```python
# shared/validation/pipeline.py
class ValidationPipeline:
    def validate(self, scenario: Scenario) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        # Run all layers - no fail-fast
        result.merge(self.syntax_validator.validate(scenario))
        result.merge(self.semantic_validator.validate(scenario))
        result.merge(self.integrity_validator.validate(scenario))
        result.merge(self.feasibility_validator.validate(scenario))
        
        return result
```

### Error Stacking
```python
# shared/validation/base.py
class ValidationResult:
    def merge(self, other: ValidationResult) -> None:
        """Stack errors from multiple validation layers."""
        self.issues.extend(other.issues)
        if other.has_errors():
            self.is_valid = False
```

### Layer Implementation Example
```python
# shared/validation/validators/integrity_validator.py
class IntegrityValidator:
    def validate(self, scenario: Scenario) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        # Validate cross-references
        locomotive_ids = {loco.id for loco in scenario.locomotives or []}
        for train in scenario.trains or []:
            if train.locomotive_id not in locomotive_ids:
                result.add_error(
                    f"Train {train.id} references non-existent locomotive '{train.locomotive_id}'",
                    field=f"trains[{train.id}].locomotive_id",
                    category=ValidationCategory.INTEGRITY,
                    suggestion=f"Use one of: {', '.join(locomotive_ids)}"
                )
        
        return result
```

## Consequences

### Positive
- **Superior User Experience**: Users see ALL validation issues at once
- **Development Efficiency**: Single validation cycle to identify all problems
- **Professional Error Reporting**: Enterprise-grade validation summaries
- **Extensible Framework**: Easy to add new validation layers or rules
- **Clear Categorization**: Issues grouped by validation concern
- **Actionable Feedback**: Each error includes specific fix suggestions

### Negative
- **Implementation Complexity**: More complex than simple fail-fast validation
- **Performance Impact**: Runs all validation layers even when errors found
- **Memory Usage**: Collects all validation issues in memory

### Risks and Mitigation
- **Risk**: Performance degradation with large scenarios
  - **Mitigation**: Validation typically completes in <100ms, acceptable for user experience
- **Risk**: Complex error messages overwhelming users
  - **Mitigation**: Clear categorization and professional formatting make errors manageable

## Validation Results

### Before (Fail-Fast)
```
❌ "Invalid scenario ID" → Fix → Run again
❌ "Missing locomotives" → Fix → Run again  
❌ "Invalid track reference" → Fix → Run again
```
**Result**: 3+ validation cycles required

### After (Error Stacking)
```
📋 Validation Summary: 3 errors, 1 warning

SYNTAX ERRORS:
- Invalid scenario ID format (Field: id)

INTEGRITY ERRORS:  
- Missing locomotives (Field: locomotives)
- Route 'R1' references non-existent track 'T99'

WARNINGS:
- Long simulation duration may impact performance
```
**Result**: 1 validation cycle shows all issues

## Compliance

This decision supports the following quality goals:
- **Usability & Accessibility** (Priority 3): Professional validation UX
- **Simulation Accuracy & Reliability** (Priority 2): Comprehensive validation prevents invalid configurations
- **Testability** (Priority 5): Layer-specific validation enables focused testing

## References

- [Building Blocks Documentation](../05-building-blocks.md#level-3-4-layer-validation-pipeline)
- [Cross-Cutting Concepts](../08-concepts.md#88-4-layer-validation-framework)

---

**Decision Date**: January 2025  
**Decision Makers**: Architecture Team  
**Implementation Status**: ✅ Complete