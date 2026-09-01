"""Helper utilities for the optimizer: scoring, type coercion and neighbor generation."""

from enum import Enum
import types
from typing import Any
from typing import Union
from typing import get_args
from typing import get_origin

from contexts.configuration.application.dtos import HoldConditionInputDTO
from contexts.configuration.application.dtos import PriorityRuleInputDTO
from contexts.configuration.application.dtos import TaskPriorityInputDTO
from contexts.configuration.domain.models.scenario import Scenario
from optimizer.parameter_model import ContinuousParameter
from optimizer.parameter_model import DiscreteParameter
from optimizer.parameter_model import GroupParameter
from optimizer.parameter_model import ListParameter
from optimizer.parameter_model import Parameter
from optimizer.parameter_model import _make_canonical
from optimizer.parameter_model import _safe_sort_key
from optimizer.summary_model import SummaryMetrics


def score(summary: SummaryMetrics, weight_completion: float = 0.9, weight_loco: float = -0.1) -> float:
    """Return the weighted objective score for a simulation summary."""
    return summary.completion_rate_pct * weight_completion + summary.loco_utilization_pct * weight_loco


def _get_underlying_type(annotation: Any) -> Any:
    """Return the non-None type of an ``Optional``/union annotation, else the annotation."""
    origin = get_origin(annotation)
    union_type = getattr(types, 'UnionType', None)
    if origin is Union or (union_type is not None and origin is union_type):
        args = get_args(annotation)
        none_type = type(None)
        non_none_args = [arg for arg in args if arg is not none_type]
        if len(non_none_args) == 1:
            return non_none_args[0]
    return annotation


def _coerce_value(value: Any, expected_type: Any) -> Any:
    if value is None:
        return None
    try:
        if isinstance(expected_type, type) and issubclass(expected_type, Enum):
            return expected_type(value)
    except TypeError:
        pass
    if expected_type in (float, int, str, bool):
        return expected_type(value)
    return value


def _to_hold_condition(raw: Any) -> HoldConditionInputDTO | None:
    """Build a HoldConditionInputDTO from a raw dict or pass through an existing one."""
    if raw is None:
        return None
    if isinstance(raw, HoldConditionInputDTO):
        return raw
    if isinstance(raw, dict):
        return HoldConditionInputDTO(
            condition=str(raw['condition']),
            threshold=float(raw.get('threshold', 0.0)),
        )
    return None


def _to_priority_rules(raw: Any) -> list[PriorityRuleInputDTO]:
    """Build a list of PriorityRuleInputDTO from a raw iterable of dicts/DTOs."""
    if raw is None:
        return []
    rules: list[PriorityRuleInputDTO] = []
    for item in raw:
        if isinstance(item, PriorityRuleInputDTO):
            rules.append(item)
        elif isinstance(item, dict):
            rules.append(
                PriorityRuleInputDTO(
                    condition=str(item['condition']),
                    threshold=float(item.get('threshold', 0.0)),
                    priority=int(item['priority']),
                )
            )
    return rules


def _to_task_priority(val: Any) -> TaskPriorityInputDTO | None:
    """Coerce a raw value into a TaskPriorityInputDTO, returning None when not possible."""
    if val is None:
        return None
    if isinstance(val, TaskPriorityInputDTO):
        return val
    if not isinstance(val, dict):
        return None

    max_hold_time = val.get('max_hold_time')
    return TaskPriorityInputDTO(
        base_priority=int(val.get('base_priority', 3)),
        rules=_to_priority_rules(val.get('rules')),
        hold_until=_to_hold_condition(val.get('hold_until')),
        max_hold_time=float(max_hold_time) if max_hold_time is not None else None,
    )


def _merge_task_priorities(current: dict[str, Any] | None, overwrite: Any) -> Any:
    """Merge a ``task_priorities`` overwrite onto the current mapping."""
    if overwrite is None:
        return {}
    if not isinstance(overwrite, dict):
        return overwrite
    merged = dict(current or {})
    for task_type, raw in overwrite.items():
        if raw is None:
            merged.pop(task_type, None)
            continue
        dto = _to_task_priority(raw)
        if dto is not None:
            merged[task_type] = dto
    return merged


def convert(parameter_overwrite: dict[str, Any], scenario: Scenario) -> Scenario:
    """Apply a parameter override mapping onto ``scenario`` and return the updated copy."""
    updates: dict[str, Any] = {}
    model_fields = type(scenario).model_fields

    for key, value in parameter_overwrite.items():
        if key == 'task_priorities':
            updates[key] = _merge_task_priorities(scenario.task_priorities, value)
        elif key in model_fields:
            underlying = _get_underlying_type(model_fields[key].annotation)
            updates[key] = _coerce_value(value, underlying) if underlying is not None else value
        else:
            updates[key] = value

    return scenario.model_copy(update=updates)


def _group_neighbors(param: GroupParameter, current_val: Any) -> list[Any]:
    """Return neighbors of a GroupParameter value by varying one sub-field at a time."""
    neighbors: list[Any] = []
    if current_val is None:
        first = next((val for val in param.iter_values() if val is not None), None)
        if first is not None:
            neighbors.append(first)
        return neighbors

    if param.optional:
        neighbors.append(None)

    for key, sub_param in param.params.items():
        for sub_neighbor in get_neighbors(sub_param, current_val.get(key)):
            new_val = dict(current_val)
            new_val[key] = sub_neighbor
            neighbors.append(new_val)
    return neighbors


def _list_neighbors(param: ListParameter, current_val: Any) -> list[Any]:
    """Return neighbors of a ListParameter value, deduplicated by canonical form."""
    neighbors: list[Any] = []
    slot_count = len(param.slots)
    slot_vals = list(current_val) + [None] * (slot_count - len(current_val))

    seen_configs: set[Any] = set()
    for i in range(slot_count):
        for sub_neighbor in get_neighbors(param.slots[i], slot_vals[i]):
            new_slots = list(slot_vals)
            new_slots[i] = sub_neighbor

            filtered = [(_make_canonical(x), _safe_sort_key(_make_canonical(x)), x) for x in new_slots if x is not None]
            filtered.sort(key=lambda item: item[1])
            canonical_combo = tuple(item[0] for item in filtered)
            if canonical_combo not in seen_configs:
                seen_configs.add(canonical_combo)
                neighbors.append([item[2] for item in filtered])
    return neighbors


def get_neighbors(param: Parameter[Any], current_val: Any) -> list[Any]:
    """Recursively generate neighboring values by varying exactly one sub-parameter field."""
    if isinstance(param, DiscreteParameter):
        return [v for v in param.values if v != current_val]
    if isinstance(param, ContinuousParameter):
        return [v for v in param.iter_values() if v != current_val]
    if isinstance(param, GroupParameter):
        return _group_neighbors(param, current_val)
    if isinstance(param, ListParameter):
        return _list_neighbors(param, current_val)
    return []
