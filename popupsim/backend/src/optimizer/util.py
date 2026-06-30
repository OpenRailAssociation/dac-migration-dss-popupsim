
from enum import Enum
import types
from typing import Any, Union, get_args, get_origin

from contexts.configuration.application.dtos import (
    HoldConditionInputDTO,
    PriorityRuleInputDTO,
    TaskPriorityInputDTO,
)
from contexts.configuration.domain.models.scenario import Scenario
from optimizer.summary_model import SummaryMetrics



from optimizer.parameter_model import (
    Parameter,
    GroupParameter,
    ListParameter,
    DiscreteParameter,
    ContinuousParameter,
    _make_canonical,
    _safe_sort_key,
)

def score(summary: SummaryMetrics, weight_completion: float = 0.9, weight_loco: float = -0.1) -> float:
    return summary.completion_rate_pct * weight_completion + summary.loco_utilization_pct * weight_loco


def _get_underlying_type(annotation: Any) -> Any:
    origin = get_origin(annotation)
    UnionType = getattr(types, "UnionType", None)
    if origin is Union or (UnionType is not None and origin is UnionType):
        args = get_args(annotation)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
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


def _to_task_priority(val: Any) -> TaskPriorityInputDTO | None:
    if val is None:
        return None
    if isinstance(val, TaskPriorityInputDTO):
        return val
    if isinstance(val, dict):
        base_priority = val.get("base_priority", 3)
        max_hold_time = val.get("max_hold_time")

        hold_until = None
        hold_until_val = val.get("hold_until")
        if hold_until_val is not None:
            if isinstance(hold_until_val, HoldConditionInputDTO):
                hold_until = hold_until_val
            elif isinstance(hold_until_val, dict):
                hold_until = HoldConditionInputDTO(
                    condition=str(hold_until_val["condition"]),
                    threshold=float(hold_until_val.get("threshold", 0.0)),
                )

        rules = []
        rules_val = val.get("rules")
        if rules_val is not None:
            for r in rules_val:
                if r is None:
                    continue
                if isinstance(r, PriorityRuleInputDTO):
                    rules.append(r)
                elif isinstance(r, dict):
                    rules.append(
                        PriorityRuleInputDTO(
                            condition=str(r["condition"]),
                            threshold=float(r.get("threshold", 0.0)),
                            priority=int(r["priority"]),
                        )
                    )

        return TaskPriorityInputDTO(
            base_priority=int(base_priority),
            rules=rules,
            hold_until=hold_until,
            max_hold_time=float(max_hold_time) if max_hold_time is not None else None,
        )
    return None


def convert(parameter_overwrite: dict[str, Any], scenario: Scenario) -> Scenario:
    updates = {}
    model_fields = Scenario.model_fields

    for k, v in parameter_overwrite.items():
        if k == "task_priorities":
            if v is None:
                updates["task_priorities"] = {}
            elif isinstance(v, dict):
                new_priorities = dict(scenario.task_priorities or {})
                for task_type, p_val in v.items():
                    if p_val is None:
                        new_priorities.pop(task_type, None)
                    else:
                        dto = _to_task_priority(p_val)
                        if dto is not None:
                            new_priorities[task_type] = dto
                updates["task_priorities"] = new_priorities
            else:
                updates["task_priorities"] = v
        else:
            if k in model_fields:
                ann = model_fields[k].annotation
                underlying = _get_underlying_type(ann)
                if underlying is not None:
                    updates[k] = _coerce_value(v, underlying)
                else:
                    updates[k] = v
            else:
                updates[k] = v

    return scenario.model_copy(update=updates)


def get_neighbors(param: Parameter[Any], current_val: Any) -> list[Any]:
    """Recursively generate neighboring values by varying exactly one sub-parameter field."""
    if isinstance(param, DiscreteParameter):
        return [v for v in param.values if v != current_val]

    if isinstance(param, ContinuousParameter):
        return [v for v in param.iter_values() if v != current_val]

    if isinstance(param, GroupParameter):
        neighbors = []
        if current_val is None:
            for val in param.iter_values():
                if val is not None:
                    neighbors.append(val)
                    break
            return neighbors

        if param.optional:
            neighbors.append(None)

        for k, sub_param in param.params.items():
            sub_val = current_val.get(k)
            for sub_neighbor in get_neighbors(sub_param, sub_val):
                new_val = dict(current_val)
                new_val[k] = sub_neighbor
                neighbors.append(new_val)
        return neighbors

    if isinstance(param, ListParameter):
        neighbors = []
        m = len(param.slots)
        slot_vals = list(current_val) + [None] * (m - len(current_val))

        seen_configs = set()
        for i in range(m):
            sub_param = param.slots[i]
            sub_val = slot_vals[i]
            for sub_neighbor in get_neighbors(sub_param, sub_val):
                new_slots = list(slot_vals)
                new_slots[i] = sub_neighbor

                filtered = []
                for x in new_slots:
                    if x is not None:
                        c = _make_canonical(x)
                        k = _safe_sort_key(c)
                        filtered.append((c, k, x))
                filtered.sort(key=lambda item: item[1])
                canonical_combo = tuple(item[0] for item in filtered)
                if canonical_combo not in seen_configs:
                    seen_configs.add(canonical_combo)
                    neighbors.append([item[2] for item in filtered])
        return neighbors

    return []

