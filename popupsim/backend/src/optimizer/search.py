"""Two-phase adaptive coordinate search over scenario parameters.

Phase 1 draws a pool of random configurations and evaluates them in parallel.
Phase 2 runs coordinate descent from the best elites, varying one task-priority
field at a time. Every evaluated configuration is cached in an
:class:`EvalRecord` keyed by a canonical JSON representation so duplicates are
never simulated twice.
"""

import copy
from dataclasses import dataclass
from dataclasses import field
import json
from pathlib import Path
import random
from typing import Any

from contexts.configuration.domain.models.scenario import Scenario
from optimizer.harness import run_parallel
from optimizer.harness import run_simulation
from optimizer.parameter_model import GroupParameter
from optimizer.problem_space import parameter_config
from optimizer.util import convert
from optimizer.util import get_neighbors

TASK_NAMES = (
    'collection_to_retrofit',
    'retrofit_to_workshop',
    'workshop_to_retrofitted',
    'retrofitted_to_parking',
)


@dataclass(frozen=True)
class SearchConfig:
    """Tuning knobs and scoring weights for an optimization run."""

    seed: int = 42
    n_random: int = 500
    k_starts: int = 5
    max_rounds: int = 5
    weight_completion: float = 0.9
    weight_loco: float = -0.1
    n_workers: int | None = None


@dataclass(frozen=True)
class EvalRecord:
    """Evaluated configuration with its score and headline metrics."""

    score: float
    completion_rate_pct: float
    loco_utilization_pct: float
    params: dict[str, Any]


@dataclass
class OptimizationResult:
    """Outcome of an optimization run."""

    initial: EvalRecord
    records: dict[str, EvalRecord] = field(default_factory=dict)

    def ranked(self) -> list[EvalRecord]:
        """Return all evaluated records sorted by descending score."""
        return sorted(self.records.values(), key=lambda r: r.score, reverse=True)


def _serialize_enums(obj: Any) -> Any:
    """Recursively replace enum values with their ``.value`` for JSON output."""
    if isinstance(obj, dict):
        return {k: _serialize_enums(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_enums(x) for x in obj]
    if hasattr(obj, 'value'):
        return obj.value
    return obj


def config_key(params: dict[str, Any]) -> str:
    """Return a canonical, order-independent string key for a configuration."""
    return json.dumps(_serialize_enums(params), sort_keys=True)


def _initial_record(scenario: Scenario, scenario_dir: Path, config: SearchConfig) -> EvalRecord:
    """Evaluate the unmodified scenario and return its record."""
    summary, score, _scenario = run_simulation(
        scenario_dir, weight_completion=config.weight_completion, weight_loco=config.weight_loco
    )
    params = {
        'task_priorities': {
            name: (dto.model_dump() if dto is not None else None) for name, dto in scenario.task_priorities.items()
        }
    }
    return EvalRecord(score, summary.completion_rate_pct, summary.loco_utilization_pct, params)


def _sample_pool(rng: random.Random, n_random: int, seen: dict[str, EvalRecord]) -> list[dict[str, Any]]:
    """Draw up to ``n_random`` unique, unseen configurations from the search space."""
    samples: list[dict[str, Any]] = []
    seen_in_pool: set[str] = set()
    attempts = 0
    while len(samples) < n_random and attempts < n_random * 10:
        attempts += 1
        candidate = parameter_config.sample_value(rng)
        if candidate is None:
            raise RuntimeError('Failed to sample parameters. Top-level parameters must not be optional.')
        key = config_key(candidate)
        if key in seen or key in seen_in_pool:
            continue
        seen_in_pool.add(key)
        samples.append(candidate)
    return samples


def _evaluate_batch(
    scenario: Scenario,
    scenario_dir: Path,
    params_batch: list[dict[str, Any]],
    config: SearchConfig,
) -> dict[str, EvalRecord]:
    """Run a batch of configurations in parallel and return their records by key."""
    scenarios = [convert(params, scenario) for params in params_batch]
    results = run_parallel(
        scenario_dir,
        scenarios,
        weight_completion=config.weight_completion,
        weight_loco=config.weight_loco,
        max_workers=config.n_workers,
    )
    records: dict[str, EvalRecord] = {}
    for params, result in zip(params_batch, results, strict=True):
        if result is None:
            continue
        summary, score, _scenario = result
        records[config_key(params)] = EvalRecord(
            score, summary.completion_rate_pct, summary.loco_utilization_pct, params
        )
    return records


def _task_config() -> GroupParameter:
    """Return the task-priorities sub-parameter of the search space."""
    task_priorities = parameter_config.params['task_priorities']
    if not isinstance(task_priorities, GroupParameter):
        raise TypeError("Expected 'task_priorities' to be a GroupParameter in the search space.")
    return task_priorities


def _neighbor_configs(current: dict[str, Any], task_name: str) -> list[dict[str, Any]]:
    """Return configurations that differ from ``current`` in one task's value."""
    task_param = _task_config().params[task_name]
    task_val = current['task_priorities'][task_name]
    neighbors: list[dict[str, Any]] = []
    for task_neighbor in get_neighbors(task_param, task_val):
        candidate = copy.deepcopy(current)
        candidate['task_priorities'][task_name] = task_neighbor
        neighbors.append(candidate)
    return neighbors


def _descend_from(
    scenario: Scenario,
    scenario_dir: Path,
    start: EvalRecord,
    config: SearchConfig,
    seen: dict[str, EvalRecord],
) -> None:
    """Run coordinate descent from ``start``, recording every evaluation in ``seen``."""
    current_params = start.params
    current_score = start.score
    for _round in range(config.max_rounds):
        improved = False
        for task_name in TASK_NAMES:
            neighbors = _neighbor_configs(current_params, task_name)
            unseen = [c for c in neighbors if config_key(c) not in seen]
            if unseen:
                seen.update(_evaluate_batch(scenario, scenario_dir, unseen, config))

            best = max(
                (seen[config_key(c)] for c in neighbors if config_key(c) in seen),
                key=lambda r: r.score,
                default=None,
            )
            if best is not None and best.score > current_score:
                current_params = best.params
                current_score = best.score
                improved = True
        if not improved:
            break


def optimize_scenario(scenario_dir: Path, config: SearchConfig | None = None) -> OptimizationResult:
    """Optimize a scenario with random search followed by coordinate descent."""
    config = config or SearchConfig()
    scenario = Scenario.model_validate_json((scenario_dir / 'scenario.json').read_text(encoding='utf-8'))

    initial = _initial_record(scenario, scenario_dir, config)
    seen: dict[str, EvalRecord] = {config_key(initial.params): initial}

    rng = random.Random(config.seed)  # noqa: S311 - search sampling, not security-sensitive
    pool = _sample_pool(rng, config.n_random, seen)
    seen.update(_evaluate_batch(scenario, scenario_dir, pool, config))

    initial_key = config_key(initial.params)
    elites = [r for r in seen.values() if config_key(r.params) != initial_key]
    elites.sort(key=lambda r: r.score, reverse=True)
    for start in elites[: config.k_starts]:
        _descend_from(scenario, scenario_dir, start, config, seen)

    return OptimizationResult(initial=initial, records=seen)


def write_results(result: OptimizationResult, results_json: Path) -> None:
    """Write all evaluated configurations to ``results_json`` sorted by score."""
    payload = [
        {
            'parameters': _serialize_enums(record.params),
            'completion': record.completion_rate_pct,
            'loco_utilization': record.loco_utilization_pct,
            'score': record.score,
        }
        for record in result.ranked()
    ]
    results_json.parent.mkdir(parents=True, exist_ok=True)
    results_json.write_text(json.dumps(payload, indent=2), encoding='utf-8')
