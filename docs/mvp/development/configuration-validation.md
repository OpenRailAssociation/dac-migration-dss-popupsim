# Configuration Validation

## Overview

**Note:** See actual implementation in `popupsim/backend/src/contexts/configuration/domain/models/`

This document describes Pydantic validation patterns used across the 4 contexts.

## Pydantic 2.0 Validation

### Basic Model

```python
from pydantic import BaseModel, Field
from datetime import date

class ScenarioConfig(BaseModel):
    """Scenario models with validation"""
    scenario_id: str = Field(
        pattern=r'^[a-zA-Z0-9_-]+$',
        min_length=1,
        max_length=50,
        description="Unique scenario identifier"
    )
    start_date: date
    end_date: date
```

### Field Validators

```python
from pydantic import field_validator

class Workshop(BaseModel):
    tracks: list[WorkshopTrack] = Field(min_length=1)

    @field_validator('tracks')
    @classmethod
    def validate_unique_track_ids(
        cls,
        tracks: list[WorkshopTrack]
    ) -> list[WorkshopTrack]:
        """Ensure all track IDs are unique"""
        track_ids = [t.id for t in tracks]
        if len(track_ids) != len(set(track_ids)):
            raise ValueError("Track IDs must be unique")
        return tracks

    @field_validator('tracks')
    @classmethod
    def validate_track_functions(
        cls,
        tracks: list[WorkshopTrack]
    ) -> list[WorkshopTrack]:
        """Ensure at least one WERKSTATTGLEIS exists"""
        functions = [t.function for t in tracks]
        if TrackFunction.WERKSTATTGLEIS not in functions:
            raise ValueError("At least one WERKSTATTGLEIS required")
        return tracks
```

### Model Validators

```python
from pydantic import model_validator

class ScenarioConfig(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def validate_date_range(self) -> 'ScenarioConfig':
        """Validate date range"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        duration = (self.end_date - self.start_date).days
        if duration > 7:
            raise ValueError("Simulation duration cannot exceed 7 days")

        return self
```

### Enum Validation

```python
from enum import Enum

class TrackFunction(str, Enum):
    """Track function types"""
    WERKSTATTGLEIS = "werkstattgleis"
    SAMMELGLEIS = "sammelgleis"
    PARKGLEIS = "parkgleis"
    WERKSTATTZUFUEHRUNG = "werkstattzufuehrung"
    WERKSTATTABFUEHRUNG = "werkstattabfuehrung"
    BAHNHOFSKOPF = "bahnhofskopf"

class WorkshopTrack(BaseModel):
    id: str
    function: TrackFunction  # Automatically validated
    capacity: int = Field(ge=1, le=20)
    retrofit_time_min: int = Field(ge=0, le=300)
```

## Validation Examples

### Valid Configuration

```python
config = ScenarioConfig(
    scenario_id="demo_scenario",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 2),
    workshop=Workshop(
        tracks=[
            WorkshopTrack(
                id="TRACK01",
                function=TrackFunction.WERKSTATTGLEIS,
                capacity=5,
                retrofit_time_min=30
            )
        ]
    ),
    train_schedule_file="schedule.csv"
)
# ✅ Valid
```

### Invalid Configurations

**Invalid scenario_id**:
```python
config = ScenarioConfig(
    scenario_id="invalid scenario!",  # Contains space and special char
    ...
)
# ❌ ValidationError: string does not match regex
```

**Invalid date range**:
```python
config = ScenarioConfig(
    start_date=date(2025, 1, 2),
    end_date=date(2025, 1, 1),  # Before start_date
    ...
)
# ❌ ValidationError: end_date must be after start_date
```

**Missing required track function**:
```python
workshop = Workshop(
    tracks=[
        WorkshopTrack(
            id="TRACK01",
            function=TrackFunction.WERKSTATTZUFUEHRUNG,  # Not WERKSTATTGLEIS
            capacity=5,
            retrofit_time_min=0
        )
    ]
)
# ❌ ValidationError: At least one WERKSTATTGLEIS required
```

**Duplicate track IDs**:
```python
workshop = Workshop(
    tracks=[
        WorkshopTrack(id="TRACK01", ...),
        WorkshopTrack(id="TRACK01", ...),  # Duplicate
    ]
)
# ❌ ValidationError: Track IDs must be unique
```

## Error Handling

### Catching Validation Errors

```python
from pydantic import ValidationError
import json

try:
    config = ScenarioConfig(**data)
except ValidationError as e:
    print("Validation failed:")
    print(e.json(indent=2))

    # Access individual errors
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Error: {error['msg']}")
        print(f"Type: {error['type']}")
```

### Error Response Format

```json
[
  {
    "type": "string_pattern_mismatch",
    "loc": ["scenario_id"],
    "msg": "String should match pattern '^[a-zA-Z0-9_-]+$'",
    "input": "invalid scenario!",
    "ctx": {
      "pattern": "^[a-zA-Z0-9_-]+$"
    }
  },
  {
    "type": "value_error",
    "loc": ["workshop", "tracks"],
    "msg": "Value error, At least one WERKSTATTGLEIS required",
    "input": [...]
  }
]
```

## Custom Validators

### Complex Business Rules

```python
class Workshop(BaseModel):
    tracks: list[WorkshopTrack]

    @model_validator(mode='after')
    def validate_capacity_distribution(self) -> 'Workshop':
        """Ensure capacity is reasonably distributed"""
        total_capacity = sum(t.capacity for t in self.tracks)

        if total_capacity < 3:
            raise ValueError("Total workshop capacity must be at least 3")

        if total_capacity > 50:
            raise ValueError("Total workshop capacity cannot exceed 50")

        # Check for balanced distribution
        capacities = [t.capacity for t in self.tracks]
        max_capacity = max(capacities)
        min_capacity = min(capacities)

        if max_capacity > min_capacity * 3:
            raise ValueError(
                "Capacity distribution too unbalanced "
                f"(max: {max_capacity}, min: {min_capacity})"
            )

        return self
```

### Cross-Field Validation

```python
class WorkshopTrack(BaseModel):
    id: str
    function: TrackFunction
    capacity: int
    retrofit_time_min: int

    @model_validator(mode='after')
    def validate_retrofit_time(self) -> 'WorkshopTrack':
        """Validate retrofit time based on function"""
        if self.function == TrackFunction.WERKSTATTGLEIS:
            if self.retrofit_time_min <= 0:
                raise ValueError(
                    "WERKSTATTGLEIS must have retrofit_time_min > 0"
                )
        else:
            if self.retrofit_time_min != 0:
                raise ValueError(
                    f"{self.function} must have retrofit_time_min = 0"
                )

        return self
```

## JSON Schema Generation

```python
# Generate JSON schema
schema = ScenarioConfig.model_json_schema()

# Save to file
with open("scenario_schema.json", "w") as f:
    json.dump(schema, f, indent=2)

# Use for validation in other tools
```

## Testing Validation

```python
import pytest
from pydantic import ValidationError

def test_valid_scenario_config() -> None:
    config = ScenarioConfig(
        scenario_id="test",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        workshop=Workshop(tracks=[...]),
        train_schedule_file="schedule.csv"
    )
    assert config.scenario_id == "test"

def test_invalid_scenario_id() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScenarioConfig(
            scenario_id="invalid scenario!",
            ...
        )

    errors = exc_info.value.errors()
    assert any(e['type'] == 'string_pattern_mismatch' for e in errors)

def test_invalid_date_range() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScenarioConfig(
            start_date=date(2025, 1, 2),
            end_date=date(2025, 1, 1),
            ...
        )

    errors = exc_info.value.errors()
    assert any('end_date must be after start_date' in e['msg'] for e in errors)
```

## Best Practices

### Do's
- ✅ Use Field() for constraints
- ✅ Use @field_validator for single-field validation
- ✅ Use @model_validator for cross-field validation
- ✅ Provide clear error messages
- ✅ Test all validation rules
- ✅ Use Enums for fixed choices

### Don'ts
- ❌ Don't use @validator (Pydantic v1 syntax)
- ❌ Don't validate in __init__
- ❌ Don't catch ValidationError silently
- ❌ Don't use complex validation logic in validators
- ❌ Don't forget to add type hints
