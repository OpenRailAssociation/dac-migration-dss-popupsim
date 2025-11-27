# ADR-003: Field Name Standardization

## Status
**ACCEPTED** - Implemented January 2025

## Context

PopUpSim codebase had inconsistent field naming patterns that created confusion and maintenance overhead:

### Problems with Inconsistent Naming
- **Prefix Inconsistency**: Mixed patterns like `scenario_id`, `wagon_id`, `workshop_id` vs `id`
- **Reference Confusion**: `track_id` vs `track` for entity references
- **Maintenance Overhead**: Different naming patterns across contexts
- **Developer Confusion**: Unclear which field name pattern to use
- **Code Duplication**: Mapping between different field name patterns

### Examples of Inconsistency
```python
# Before - Inconsistent patterns
class Scenario:
    scenario_id: str  # prefix_id pattern

class Wagon:
    wagon_id: str     # prefix_id pattern
    track_id: str     # reference with _id suffix

class Workshop:
    workshop_id: str  # prefix_id pattern
    track_id: str     # reference with _id suffix
```

## Decision

Implement **systematic field name standardization** across the entire codebase:

### Standardization Rules
1. **Entity IDs**: Use `id` (not `prefix_id`)
2. **Entity References**: Use `track` (not `track_id`) for track references
3. **Consistency**: Apply same pattern across all contexts
4. **Backward Compatibility**: Update all DTOs, domain models, and test fixtures

### Implementation Strategy
```python
# After - Consistent patterns
class Scenario:
    id: str           # standardized

class Wagon:
    id: str           # standardized
    track: str        # reference without _id suffix

class Workshop:
    id: str           # standardized
    track: str        # reference without _id suffix
```

## Alternatives Considered

### Alternative 1: Keep Existing Inconsistent Naming
- **Pros**: No refactoring required
- **Cons**: Continued confusion, maintenance overhead, poor developer experience
- **Rejected**: Technical debt would continue to grow

### Alternative 2: Use Prefix Pattern Everywhere
- **Pros**: Explicit field identification
- **Cons**: Verbose, redundant (class name already provides context)
- **Rejected**: Unnecessarily verbose for clean code

### Alternative 3: Use Full Reference Names
- **Pros**: Very explicit (`locomotive_id`, `route_id`)
- **Cons**: Verbose, inconsistent with modern naming conventions
- **Rejected**: Modern frameworks favor concise, context-aware naming

## Implementation

### Systematic Refactoring
1. **Domain Models**: Updated all entity classes
2. **DTOs**: Updated all input/output DTOs
3. **Test Fixtures**: Updated JSON test files
4. **Validation**: Updated field references in validators
5. **Analytics**: Updated collector attribute names

### Key Changes
```python
# Domain Models
class Scenario(BaseModel):
    id: str  # was: scenario_id

class Locomotive(BaseModel):
    id: str    # was: locomotive_id
    track: str # was: track_id

# DTOs
class WagonInputDTO(BaseModel):
    id: str    # was: wagon_id
    track: str # was: track_id

# Analytics
class WorkshopCollector:
    idle_time: float        # was: workshop_idle_time
    active_time: float      # was: workshop_active_time
    station_usage: dict     # was: workshop_station_usage
```

### Validation Updates
- Updated all validation error messages
- Fixed field path references in validation results
- Updated cross-reference validation logic

## Consequences

### Positive
- **Consistent Naming**: Single, clear naming pattern across codebase
- **Reduced Confusion**: Developers know which pattern to use
- **Cleaner Code**: More concise, readable field names
- **Better Maintainability**: Consistent patterns easier to maintain
- **Professional Appearance**: Modern, clean naming conventions

### Negative
- **Breaking Changes**: Existing configurations need field name updates
- **Refactoring Effort**: Required systematic updates across codebase
- **Migration Required**: Test fixtures and example scenarios updated

### Migration Impact
- **Test Fixtures**: All JSON test files updated with new field names
- **Example Scenarios**: Updated to use standardized field names
- **Documentation**: Updated to reflect new naming conventions
- **Validation**: All field references updated in validation framework

## Validation

### Before Standardization
```json
{
  "scenario_id": "test-scenario",
  "locomotives": [
    {
      "locomotive_id": "L1",
      "track_id": "PARKING_1"
    }
  ],
  "workshops": [
    {
      "workshop_id": "WS1",
      "track_id": "WORKSHOP_1"
    }
  ]
}
```

### After Standardization
```json
{
  "id": "test-scenario",
  "locomotives": [
    {
      "id": "L1",
      "track": "PARKING_1"
    }
  ],
  "workshops": [
    {
      "id": "WS1",
      "track": "WORKSHOP_1"
    }
  ]
}
```

## Compliance

This decision supports:
- **Code Quality**: Consistent, maintainable codebase
- **Developer Experience**: Clear, predictable naming patterns
- **Maintainability**: Reduced cognitive overhead for developers

## References

- [Building Blocks Documentation](../05-building-blocks.md)
- [Domain Model Documentation](../08-concepts.md#82-domain-model-with-standardized-field-names)

---

**Decision Date**: January 2025  
**Decision Makers**: Architecture Team  
**Implementation Status**: ✅ Complete