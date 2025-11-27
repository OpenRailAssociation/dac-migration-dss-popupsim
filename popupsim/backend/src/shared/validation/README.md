# PopUpSim Validation Framework

4-layer validation pipeline with comprehensive error stacking for scenario configuration validation.

## Overview

The validation framework provides **enterprise-grade validation** with superior user experience by collecting ALL validation issues across multiple layers instead of failing fast on the first error.

## Architecture

```
┌─────────────────┐
│ ValidationPipeline │
└─────────────────┘
         │
    ┌────┴────┐
    │ Layer 1 │ SYNTAX     → Field format, types, required fields
    │ Layer 2 │ SEMANTIC   → Business rules within entities  
    │ Layer 3 │ INTEGRITY  → Cross-references, data consistency
    │ Layer 4 │ FEASIBILITY → Operational constraints, simulation readiness
    └─────────┘
```

## Quick Start

```python
from shared.validation.pipeline import ValidationPipeline

# Validate scenario
pipeline = ValidationPipeline()
result = pipeline.validate(scenario)

# Check results
if not result.is_valid:
    result.print_summary()  # Shows all issues grouped by category
```

## Validation Layers

### Layer 1: SYNTAX
- Field presence and format validation
- Type checking and basic constraints
- Pattern matching (IDs, enums)

### Layer 2: SEMANTIC  
- Business rules within single entities
- Date logic and duration validation
- Strategy enum validation

### Layer 3: INTEGRITY
- Cross-reference validation (IDs exist)
- Data consistency across entities
- Duplicate ID detection

### Layer 4: FEASIBILITY
- Operational capacity constraints
- Resource allocation validation
- Simulation readiness checks

## Error Stacking Benefits

**Before (Fail-Fast):**
```
❌ "Invalid scenario ID" → Fix → Run again
❌ "Missing locomotives" → Fix → Run again  
❌ "Invalid track reference" → Fix → Run again
```

**After (Error Stacking):**
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

## ValidationResult API

```python
result = pipeline.validate(scenario)

# Check status
result.is_valid          # bool
result.has_errors()      # bool
result.has_warnings()    # bool

# Get issues
result.get_errors()      # List[ValidationIssue]
result.get_warnings()    # List[ValidationIssue]
result.get_issues_by_category(ValidationCategory.SYNTAX)

# Merge results
result.merge(other_result)

# Add issues
result.add_error("Message", field="field_name", category=ValidationCategory.SYNTAX)
result.add_warning("Message", field="field_name", category=ValidationCategory.FEASIBILITY)
```

## ValidationIssue Structure

```python
@dataclass
class ValidationIssue:
    level: ValidationLevel        # ERROR, WARNING, INFO
    message: str                 # Human-readable description
    category: ValidationCategory # SYNTAX, SEMANTIC, INTEGRITY, FEASIBILITY
    field: str | None           # Field path (e.g., "trains[0].locomotive_id")
    suggestion: str | None      # Actionable fix suggestion
```

## Integration

The validation framework integrates with:
- **Configuration Context**: Scenario loading and validation
- **ValidationCoordinator**: Cross-context validation orchestration
- **ScenarioPipeline**: Late validation in loading pipeline

## Testing Individual Layers

```python
# Test specific validation layer
result = pipeline.validate_layer(scenario, ValidationCategory.INTEGRITY)
```

## Extending Validation

Add new validators by implementing the validation interface:

```python
class CustomValidator:
    def validate(self, scenario: Scenario) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        # Add validation logic
        return result

# Register with coordinator
coordinator.add_validator(CustomValidator())
```

## Performance

- **Syntax Layer**: ~1ms (basic field checks)
- **Semantic Layer**: ~5ms (business rules)
- **Integrity Layer**: ~10ms (cross-references)
- **Feasibility Layer**: ~20ms (capacity calculations)

Total validation time: **~36ms** for comprehensive scenario validation.

## Error Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **SYNTAX** | Format validation | Invalid ID format, missing required fields |
| **SEMANTIC** | Business rules | End date before start date, negative capacity |
| **INTEGRITY** | Cross-references | Non-existent locomotive ID, duplicate IDs |
| **FEASIBILITY** | Operational constraints | Insufficient capacity, missing track types |

The validation framework ensures **robust scenario validation** with excellent developer experience through comprehensive error reporting and actionable suggestions.