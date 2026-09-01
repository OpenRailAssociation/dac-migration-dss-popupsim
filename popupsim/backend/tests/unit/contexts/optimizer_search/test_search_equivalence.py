"""Differential test: refactored optimizer.search vs the original inline algorithm.

The optimization algorithm used to live inline inside ``main.optimize`` (see
PR #431). It was extracted into :mod:`optimizer.search` during a refactor. This
test pins the behaviour by re-implementing the *original* orchestration as an
oracle and asserting that the refactored :func:`optimize_scenario` produces the
identical set of evaluated configurations and the identical ranking.

Both the oracle and the refactored code are driven by:
  * the same shared search space (``parameter_config``), neighbor generation
    (``get_neighbors``) and conversion (``convert``) — unchanged by the refactor;
  * the same deterministic stub evaluator (no real simulations are run);
  * the same random seed.

So any divergence isolates a behavioural change in the extracted orchestration.
"""

import copy
import random
from typing import Any
from typing import ClassVar

from optimizer import search
from optimizer.problem_space import parameter_config
from optimizer.util import get_neighbors
import pytest

# ---------------------------------------------------------------------------
# Deterministic stub evaluator
# ---------------------------------------------------------------------------


def _stub_score(params: dict[str, Any]) -> float:
    """Deterministic pseudo-score derived only from the configuration contents.

    Using a stable hash of the canonical key means the same configuration always
    scores the same, and the ordering across configurations is well-defined and
    reproducible, without running any simulation.
    """
    key = search.config_key(params)
    # Map the stable digest into a bounded, deterministic float score.
    digest = abs(hash(key))
    return (digest % 100_000) / 1000.0


def _key(params: dict[str, Any]) -> str:
    return search.config_key(params)


# ---------------------------------------------------------------------------
# Oracle: the original inline two-phase algorithm (from origin/main, PR #431)
# ---------------------------------------------------------------------------


def _original_optimize(seed: int, n_random: int, k_starts: int, max_rounds: int) -> dict[str, float]:
    """Re-implementation of the original main.optimize algorithm.

    Returns a mapping of ``config_key -> score`` for every evaluated
    configuration (the original's ``seen`` cache), which fully captures which
    configurations were explored and their scores.
    """
    task_names = (
        'collection_to_retrofit',
        'retrofit_to_workshop',
        'workshop_to_retrofitted',
        'retrofitted_to_parking',
    )

    # Initial configuration: the empty task-priorities baseline used by the
    # original (an unmodified scenario has no per-task overrides in the stub).
    initial_params: dict[str, Any] = {'task_priorities': dict.fromkeys(task_names)}
    seen: dict[str, float] = {_key(initial_params): _stub_score(initial_params)}

    # Phase 1: random exploration
    rng = random.Random(seed)
    samples: list[dict[str, Any]] = []
    attempts = 0
    while len(samples) < n_random and attempts < n_random * 10:
        attempts += 1
        test = parameter_config.sample_value(rng)
        if test is None:
            raise RuntimeError('Failed to sample parameters.')
        key = _key(test)
        if key in seen or any(_key(s) == key for s in samples):
            continue
        samples.append(test)

    rated_runs = [(_stub_score(p), p) for p in samples]
    rated_runs.sort(key=lambda x: x[0], reverse=True)
    for sc, param_dict in rated_runs:
        seen[_key(param_dict)] = sc

    # Phase 2: coordinate descent from top-k elites
    starts = rated_runs[:k_starts]
    for start_score, start_params in starts:
        current_params = start_params
        current_score = start_score
        for _round in range(max_rounds):
            improved = False
            for task_name in task_names:
                task_param = parameter_config.params['task_priorities'].params[task_name]
                task_val = current_params['task_priorities'][task_name]
                neighbors_task_val = get_neighbors(task_param, task_val)

                for task_neighbor in neighbors_task_val:
                    n_params = copy.deepcopy(current_params)
                    n_params['task_priorities'][task_name] = task_neighbor
                    key = _key(n_params)
                    if key not in seen:
                        seen[key] = _stub_score(n_params)

                best_neighbor = None
                best_neighbor_score = current_score
                for task_neighbor in neighbors_task_val:
                    n_params = copy.deepcopy(current_params)
                    n_params['task_priorities'][task_name] = task_neighbor
                    s = seen.get(_key(n_params), float('-inf'))
                    if s > best_neighbor_score:
                        best_neighbor_score = s
                        best_neighbor = n_params
                if best_neighbor is not None:
                    current_params = best_neighbor
                    current_score = best_neighbor_score
                    improved = True
            if not improved:
                break

    return seen


# ---------------------------------------------------------------------------
# Fixtures / harness stubbing
# ---------------------------------------------------------------------------


@pytest.fixture
def stubbed_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the search module's simulation calls with the deterministic stub.

    ``optimize_scenario`` reads scenario.task_priorities and calls
    run_simulation / run_parallel. We stub all three so the differential test is
    fast, deterministic and simulation-free.
    """

    class _StubSummary:
        def __init__(self, score: float) -> None:
            # completion/loco values are irrelevant to the equivalence check;
            # only the score drives the algorithm's decisions.
            self.completion_rate_pct = score
            self.loco_utilization_pct = 0.0

    class _StubScenario:
        # Matches the empty baseline the oracle uses for the initial config.
        task_priorities: ClassVar[dict[str, Any]] = {
            'collection_to_retrofit': None,
            'retrofit_to_workshop': None,
            'workshop_to_retrofitted': None,
            'retrofitted_to_parking': None,
        }

    def fake_model_validate_json(_text: str) -> _StubScenario:
        return _StubScenario()

    def fake_run_simulation(_scenario_dir: Any, **_kwargs: Any) -> tuple[Any, float, Any]:
        params = {'task_priorities': dict(_StubScenario.task_priorities)}
        score = _stub_score(params)
        return _StubSummary(score), score, None

    def fake_convert(params: dict[str, Any], _scenario: Any) -> dict[str, Any]:
        # In the stub world a "scenario" is just its params; carry them through
        # so run_parallel can score them.
        return params

    def fake_run_parallel(_scenario_dir: Any, scenarios: list[Any], **_kwargs: Any) -> list[Any]:
        results = []
        for params in scenarios:
            score = _stub_score(params)
            results.append((_StubSummary(score), score, None))
        return results

    monkeypatch.setattr(search.Scenario, 'model_validate_json', staticmethod(fake_model_validate_json))
    monkeypatch.setattr(search, 'run_simulation', fake_run_simulation)
    monkeypatch.setattr(search, 'run_parallel', fake_run_parallel)
    monkeypatch.setattr(search, 'convert', fake_convert)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# Small budget keeps the neighbor enumeration fast while still exercising both
# phases (random pool + multi-start coordinate descent).
_CONFIG = search.SearchConfig(seed=42, n_random=25, k_starts=3, max_rounds=3)


def test_refactored_matches_original_algorithm(tmp_path, stubbed_harness) -> None:
    """Refactored optimize_scenario explores the same configs and scores as the original."""
    (tmp_path / 'scenario.json').write_text('{}', encoding='utf-8')

    result = search.optimize_scenario(tmp_path, _CONFIG)
    refactored_seen = {key: rec.score for key, rec in result.records.items()}

    oracle_seen = _original_optimize(
        seed=_CONFIG.seed,
        n_random=_CONFIG.n_random,
        k_starts=_CONFIG.k_starts,
        max_rounds=_CONFIG.max_rounds,
    )

    # Same set of evaluated configurations...
    assert set(refactored_seen) == set(oracle_seen)
    # ...with identical scores for each.
    assert refactored_seen == oracle_seen


def test_ranking_matches_original(tmp_path, stubbed_harness) -> None:
    """The ranked ordering of configurations is identical to the original's."""
    (tmp_path / 'scenario.json').write_text('{}', encoding='utf-8')

    result = search.optimize_scenario(tmp_path, _CONFIG)
    refactored_ranked = [(key, rec.score) for key, rec in ((search.config_key(r.params), r) for r in result.ranked())]

    oracle_seen = _original_optimize(
        seed=_CONFIG.seed,
        n_random=_CONFIG.n_random,
        k_starts=_CONFIG.k_starts,
        max_rounds=_CONFIG.max_rounds,
    )
    oracle_ranked = sorted(oracle_seen.items(), key=lambda kv: kv[1], reverse=True)

    # Compare by score sequence (ties may reorder keys, so compare scores).
    assert [score for _, score in refactored_ranked] == [score for _, score in oracle_ranked]


def test_optimize_is_deterministic(tmp_path, stubbed_harness) -> None:
    """Two runs with the same seed produce identical evaluated configurations."""
    (tmp_path / 'scenario.json').write_text('{}', encoding='utf-8')

    first = search.optimize_scenario(tmp_path, _CONFIG)
    second = search.optimize_scenario(tmp_path, _CONFIG)

    assert {k: r.score for k, r in first.records.items()} == {k: r.score for k, r in second.records.items()}


def test_no_duplicate_configurations_evaluated(tmp_path, stubbed_harness) -> None:
    """The seen cache guarantees each configuration key is unique (no re-simulation)."""
    (tmp_path / 'scenario.json').write_text('{}', encoding='utf-8')

    result = search.optimize_scenario(tmp_path, _CONFIG)
    keys = [search.config_key(r.params) for r in result.records.values()]
    assert len(keys) == len(set(keys))
