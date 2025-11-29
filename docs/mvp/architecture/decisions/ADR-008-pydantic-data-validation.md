# ADR-008: Pydantic for Data Validation

**Status:** IMPLEMENTED - 2025-01-15

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

## Implementation in MVP

### Domain Models with Pydantic
```python
# configuration/domain/models/scenario.py
class Scenario(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    start_date: datetime
    end_date: datetime
    trains: list[Train] | None = None
    wagons: list[Wagon] | None = None
    
    @field_validator('end_date')
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

# workshop_operations/domain/entities/wagon.py
class Wagon(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    track: str
    length: float = Field(gt=0, le=30)
    needs_retrofit: bool = True
    status: WagonStatus = WagonStatus.ARRIVED
```

### Validation Integration
```python
# shared/validation/validators/syntax_validator.py
class SyntaxValidator:
    def validate(self, scenario: Scenario) -> ValidationResult:
        try:
            # Pydantic validation happens automatically
            validated = Scenario.model_validate(scenario.model_dump())
            return ValidationResult(is_valid=True)
        except ValidationError as e:
            return self._convert_pydantic_errors(e)
```

## Consequences

### Achieved
- ✅ **Type Safety**: Automatic validation with Python type hints
- ✅ **Clear Error Messages**: Detailed validation errors with field paths
- ✅ **JSON Schema**: Auto-generated schemas for documentation
- ✅ **IDE Support**: Excellent autocomplete and type checking
- ✅ **Performance**: Fast validation with Rust-based core
- ✅ **Integration**: Seamless integration with 4-layer validation framework

### Files Implementing This Decision
- `configuration/domain/models/` - All domain models use Pydantic
- `workshop_operations/domain/entities/` - Entity models with validation
- `shared/validation/validators/syntax_validator.py` - Pydantic integration