"""Adaptive optimizer for PopUpSim scenarios.

Searches the scenario parameter space in two phases:

  - **Exploration**: uniform random sampling across all strategy enums and
    continuous thresholds.
  - **Exploitation**: biased sampling guided by the top-K (elite) trials —
    most-common value for discrete parameters, Gaussian perturbation around
    the elite mean for continuous parameters.

The composite objective is a weighted sum of three normalised metrics:
  * completion_rate   (fraction of eligible wagons successfully processed)
  * throughput_rate   (wagons / hour, normalised against the best seen so far)
  * workshop_utilization (%, divided by 100)
"""

from collections.abc import Callable
from collections.abc import Generator
from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import contextlib
from dataclasses import dataclass
from dataclasses import field
import json
import logging
from pathlib import Path
import random
import shutil
import time
from typing import Any

from application.simulation_service import SimulationApplicationService
from contexts.configuration.domain.models.scenario import LocoDeliveryStrategy
from contexts.configuration.domain.models.scenario import LocoPriorityStrategy
from contexts.configuration.domain.models.scenario import Scenario
from shared.domain.value_objects.selection_strategy import SelectionStrategy
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Parameter space
# ---------------------------------------------------------------------------

_STRATEGY_VALUES: list[SelectionStrategy] = list(SelectionStrategy)


@dataclass(frozen=True)
class DiscreteParam:
    """A categorical (enum) optimization parameter."""

    name: str
    values: list[Any]


@dataclass(frozen=True)
class ContinuousParam:
    """A continuous (float) optimization parameter."""

    name: str
    low: float
    high: float


#: Full tunable parameter space used by the optimizer.
PARAMETER_SPACE: list[DiscreteParam | ContinuousParam] = [
    DiscreteParam('collection_track_strategy', _STRATEGY_VALUES),
    DiscreteParam('retrofit_selection_strategy', _STRATEGY_VALUES),
    DiscreteParam('retrofitted_selection_strategy', _STRATEGY_VALUES),
    DiscreteParam('workshop_selection_strategy', _STRATEGY_VALUES),
    DiscreteParam('parking_selection_strategy', _STRATEGY_VALUES),
    DiscreteParam('loco_delivery_strategy', list(LocoDeliveryStrategy)),
    DiscreteParam('loco_priority_strategy', list(LocoPriorityStrategy)),
    ContinuousParam('parking_normal_threshold', 0.1, 0.5),
    ContinuousParam('parking_critical_threshold', 0.5, 0.95),
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OptimizationObjective:
    """Composite objective function with configurable metric weights.

    The three metrics are each normalised to ``[0, 1]`` before weighting:

    * ``completion_rate`` is already in ``[0, 1]``.
    * ``throughput_rate_per_hour`` is divided by the highest value seen so
      far across all trials (running normalisation).
    * ``workshop_utilization`` is a percentage, divided by 100.

    Weights do not need to sum to 1, but the resulting score is most
    interpretable when they do.
    """

    weight_completion: float = 0.5
    weight_throughput: float = 0.3
    weight_utilization: float = 0.2

    def score(self, metrics: dict[str, Any], throughput_ref: float) -> float:
        """Return a composite ``[0, 1]`` score from raw simulation metrics.

        Parameters
        ----------
        metrics:
            Dict as produced by ``_read_summary_metrics`` (fields from
            ``summary_metrics.json``).
        throughput_ref:
            Maximum throughput seen across all trials so far (used to
            normalise the throughput component).
        """
        completion = float(metrics.get('completion_rate', 0.0))
        throughput = float(metrics.get('throughput_rate_per_hour', 0.0))
        utilization = float(metrics.get('workshop_utilization', 0.0)) / 100.0
        norm_throughput = min((throughput / throughput_ref) if throughput_ref > 0.0 else 0.0, 1.0)
        return (
            self.weight_completion * completion
            + self.weight_throughput * norm_throughput
            + self.weight_utilization * utilization
        )


@dataclass
class TrialResult:
    """Outcome of a single optimizer trial."""

    trial_id: int
    params: dict[str, Any]
    metrics: dict[str, Any]
    score: float
    success: bool
    wall_time: float = field(default=0.0)


@dataclass
class _TrialSpec:
    """Trial specification passed to a worker process (must be picklable)."""

    trial_id: int
    params: dict[str, Any]
    base_scenario: Scenario
    trial_dir: Path
    until: float


def _build_scenario_from_params(base_scenario: Scenario, params: dict[str, Any]) -> Scenario:
    """Apply *params* overrides to *base_scenario*, enforcing threshold ordering."""
    overrides: dict[str, Any] = dict(params)
    normal = float(overrides.get('parking_normal_threshold', base_scenario.parking_normal_threshold))
    critical = float(overrides.get('parking_critical_threshold', base_scenario.parking_critical_threshold))
    if normal >= critical:
        overrides['parking_normal_threshold'] = critical * 0.5
    return base_scenario.model_copy(update=overrides)


def _run_trial_in_worker(spec: _TrialSpec) -> tuple[int, dict[str, Any], bool, float]:
    """Run one simulation trial in a worker process.

    Top-level function (picklable for ``ProcessPoolExecutor``).

    Returns
    -------
    tuple[int, dict[str, Any], bool, float]
        ``(trial_id, metrics, success, wall_time_seconds)``
    """
    t0 = time.monotonic()
    try:
        spec.trial_dir.mkdir(parents=True, exist_ok=True)
        scenario = _build_scenario_from_params(spec.base_scenario, spec.params)
        with _suppress_logging():
            service = SimulationApplicationService(scenario, spec.trial_dir)
            sim_result = service.execute(spec.until)
        if not sim_result.success:
            return spec.trial_id, {}, False, time.monotonic() - t0
        retrofit_ctx = service.contexts.get('retrofit_workflow')
        if retrofit_ctx is not None and hasattr(retrofit_ctx, 'export_events'):
            retrofit_ctx.export_events(str(spec.trial_dir))
        return spec.trial_id, _read_summary_metrics(spec.trial_dir), True, time.monotonic() - t0
    except Exception:  # pylint: disable=broad-exception-caught
        return spec.trial_id, {}, False, time.monotonic() - t0


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------


class AdaptiveOptimizer:
    """Two-phase adaptive optimizer for PopUpSim scenario parameters.

    **Phase 1 - Exploration**: uniform random sampling across the full
    parameter space defined in :data:`PARAMETER_SPACE`.

    **Phase 2 - Exploitation**: biased sampling guided by the elite
    (top-K) successful trials:

    * Discrete parameters: the most frequent value among elite results is
      chosen with 70 % probability; the remaining 30 % draws uniformly
      from all valid values.
    * Continuous parameters: a Gaussian centred on the elite mean with
      sigma = 20 % of the parameter range is used, clipped to ``[low, high]``.

    Parameters
    ----------
    base_scenario:
        Template scenario — parameter overrides are applied via
        ``Scenario.model_copy(update=...)``.
    objective:
        Composite objective weights.
    work_dir:
        Working directory; each trial writes to ``work_dir/trial_NNN/``.
        The caller is responsible for cleaning up or keeping these
        subdirectories.
    seed:
        Optional random seed for reproducibility.
    """

    def __init__(
        self,
        base_scenario: Scenario,
        objective: OptimizationObjective,
        work_dir: Path,
        seed: int | None = None,
    ) -> None:
        self.base_scenario = base_scenario
        self.objective = objective
        self.work_dir = work_dir
        self._rng = random.Random(seed)  # noqa: S311
        self._results: list[TrialResult] = []
        self._throughput_ref: float = 1.0
        self._until: float = timedelta_to_sim_ticks(base_scenario.end_date - base_scenario.start_date)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        n_explore: int = 500,
        n_exploit: int = 50,
        phase_callback: Callable[[int, int, int], None] | None = None,
        max_workers: int = 1,
        progress_callback: Callable[[TrialResult, int, int], None] | None = None,
    ) -> TrialResult | None:
        """Run *n_explore* + *n_exploit* simulations and return the best result.

        Parameters
        ----------
        n_explore:
            Number of uniform random exploration trials (Phase 1).
        n_exploit:
            Number of adaptive exploitation trials guided by the Phase 1
            elite results (Phase 2).
        phase_callback:
            Optional callable invoked at the start of each phase with
            ``(phase_number, n_phase_trials, n_total_trials)``.
        max_workers:
            Number of parallel worker processes.  ``1`` (default) runs
            trials sequentially; values ``> 1`` use ``ProcessPoolExecutor``.
            Pass ``os.cpu_count()`` to utilise all available cores.
        progress_callback:
            Optional callable invoked after every completed trial with
            ``(result, trial_id, total_trials)``.

        Returns
        -------
        TrialResult | None
            Best-scoring successful trial, or ``None`` if every trial failed.
        """
        n_explore = max(1, n_explore)
        n_exploit = max(0, n_exploit)
        n_total = n_explore + n_exploit
        elite_k = max(1, n_explore // 3)

        logger.info(
            'Optimizer: %d total trials (%d explore / %d exploit, elite_k=%d, workers=%d)',
            n_total,
            n_explore,
            n_exploit,
            elite_k,
            max_workers,
        )

        # Phase 1 - random exploration
        if phase_callback is not None:
            phase_callback(1, n_explore, n_total)
        phase1_samples: list[tuple[int, dict[str, Any]]] = [(i, self._sample_random()) for i in range(n_explore)]
        self._run_phase(phase1_samples, n_total, max_workers, progress_callback)

        # Phase 2 - adaptive exploitation
        if n_exploit > 0:
            if phase_callback is not None:
                phase_callback(2, n_exploit, n_total)
            elite = self._top_k_results(elite_k)
            phase2_samples: list[tuple[int, dict[str, Any]]] = [
                (n_explore + i, self._sample_adaptive(elite)) for i in range(n_exploit)
            ]
            self._run_phase(phase2_samples, n_total, max_workers, progress_callback)

        return self._best_result()

    def sorted_results(self) -> list[TrialResult]:
        """All trial results sorted best-first by score."""
        return sorted(self._results, key=lambda r: r.score, reverse=True)

    # ------------------------------------------------------------------
    # Phase dispatch
    # ------------------------------------------------------------------

    def _run_phase(  # pylint: disable=too-many-arguments
        self,
        samples: list[tuple[int, dict[str, Any]]],
        n_total: int,
        max_workers: int,
        progress_callback: Callable[[TrialResult, int, int], None] | None,
    ) -> None:
        """Run a pre-sampled batch sequentially or via ``ProcessPoolExecutor``."""
        if max_workers < 2:
            for trial_id, params in samples:
                self._run_and_record(trial_id, n_total, params, progress_callback)
            return

        specs = [
            _TrialSpec(
                trial_id=trial_id,
                params=params,
                base_scenario=self.base_scenario,
                trial_dir=self.work_dir / f'trial_{trial_id:03d}',
                until=self._until,
            )
            for trial_id, params in samples
        ]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures: dict[Future[tuple[int, dict[str, Any], bool, float]], _TrialSpec] = {
                executor.submit(_run_trial_in_worker, spec): spec for spec in specs
            }
            for future in as_completed(futures):
                self._record_future(futures[future], future, n_total, progress_callback)

    def _record_future(  # pylint: disable=too-many-arguments
        self,
        spec: '_TrialSpec',
        future: 'Future[tuple[int, dict[str, Any], bool, float]]',
        n_total: int,
        progress_callback: Callable[[TrialResult, int, int], None] | None,
    ) -> None:
        """Score and record one completed parallel future."""
        try:
            trial_id, metrics, success, wall = future.result()
        except Exception:  # pylint: disable=broad-exception-caught
            trial_id, metrics, success, wall = spec.trial_id, {}, False, 0.0
        score = self.objective.score(metrics, self._throughput_ref) if success else -1.0
        if success:
            self._throughput_ref = max(self._throughput_ref, float(metrics.get('throughput_rate_per_hour', 0.0)))
        result = TrialResult(
            trial_id=trial_id, params=spec.params, metrics=metrics, score=score, success=success, wall_time=wall
        )
        self._results.append(result)
        logger.debug('Trial %03d: score=%.4f success=%s wall=%.1fs', trial_id, score, success, wall)
        if progress_callback is not None:
            progress_callback(result, trial_id, n_total)

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def _sample_random(self) -> dict[str, Any]:
        """Uniform random sample from the full parameter space."""
        params: dict[str, Any] = {}
        for param in PARAMETER_SPACE:
            if isinstance(param, DiscreteParam):
                params[param.name] = self._rng.choice(param.values)
            else:
                params[param.name] = self._rng.uniform(param.low, param.high)
        return params

    def _sample_adaptive(self, elite: list[TrialResult]) -> dict[str, Any]:
        """Biased sample guided by the elite trial results."""
        if not elite:
            return self._sample_random()
        params: dict[str, Any] = {}
        for param in PARAMETER_SPACE:
            if isinstance(param, DiscreteParam):
                params[param.name] = self._sample_discrete_adaptive(param, elite)
            else:
                params[param.name] = self._sample_continuous_adaptive(param, elite)
        return params

    def _sample_discrete_adaptive(self, param: DiscreteParam, elite: list[TrialResult]) -> Any:
        """70 % probability: most-frequent elite value; 30 %: uniform random."""
        counts: dict[Any, int] = {}
        for r in elite:
            val = r.params.get(param.name)
            if val is not None:
                counts[val] = counts.get(val, 0) + 1
        if not counts:
            return self._rng.choice(param.values)
        if self._rng.random() < 0.7:
            return max(counts, key=lambda v: counts[v])
        return self._rng.choice(param.values)

    def _sample_continuous_adaptive(self, param: ContinuousParam, elite: list[TrialResult]) -> float:
        """Gaussian around the elite mean, clipped to ``[low, high]``."""
        vals = [float(r.params[param.name]) for r in elite if param.name in r.params]
        if not vals:
            return self._rng.uniform(param.low, param.high)
        mean_val = sum(vals) / len(vals)
        std = (param.high - param.low) * 0.2
        value = self._rng.gauss(mean_val, std)
        return max(param.low, min(param.high, value))

    # ------------------------------------------------------------------
    # Trial execution
    # ------------------------------------------------------------------

    def _run_and_record(
        self,
        trial_id: int,
        total: int,
        params: dict[str, Any],
        progress_callback: Callable[[TrialResult, int, int], None] | None,
    ) -> None:
        """Execute one trial, score it, append to results, and call callback."""
        t0 = time.monotonic()
        metrics, success = self._execute_trial(trial_id, params)
        wall = time.monotonic() - t0

        score = self.objective.score(metrics, self._throughput_ref) if success else -1.0
        if success:
            throughput = float(metrics.get('throughput_rate_per_hour', 0.0))
            self._throughput_ref = max(self._throughput_ref, throughput)

        result = TrialResult(
            trial_id=trial_id,
            params=params,
            metrics=metrics,
            score=score,
            success=success,
            wall_time=wall,
        )
        self._results.append(result)
        logger.debug('Trial %03d: score=%.4f success=%s wall=%.1fs', trial_id, score, success, wall)

        if progress_callback is not None:
            progress_callback(result, trial_id, total)

    def _execute_trial(self, trial_id: int, params: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Build a scenario variant, run the simulation, return ``(metrics, success)``."""
        trial_dir = self.work_dir / f'trial_{trial_id:03d}'
        trial_dir.mkdir(parents=True, exist_ok=True)

        try:
            scenario = _build_scenario_from_params(self.base_scenario, params)

            with _suppress_logging():
                service = SimulationApplicationService(scenario, trial_dir)
                result = service.execute(self._until)

            if not result.success:
                return {}, False

            # Export events to get summary_metrics.json
            retrofit_ctx = service.contexts.get('retrofit_workflow')
            if retrofit_ctx is not None and hasattr(retrofit_ctx, 'export_events'):
                retrofit_ctx.export_events(str(trial_dir))

            return _read_summary_metrics(trial_dir), True

        except Exception:  # pylint: disable=broad-exception-caught
            logger.debug('Trial %03d raised an exception', trial_id, exc_info=True)
            return {}, False

    def _build_scenario(self, params: dict[str, Any]) -> Scenario:
        """Apply parameter overrides to the base scenario (delegates to module-level helper)."""
        return _build_scenario_from_params(self.base_scenario, params)

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    def _top_k_results(self, k: int) -> list[TrialResult]:
        """Return the top-*k* successful results sorted by score."""
        successful = [r for r in self._results if r.success]
        return sorted(successful, key=lambda r: r.score, reverse=True)[:k]

    def _best_result(self) -> TrialResult | None:
        """Return the single best successful result, or ``None``."""
        top = self._top_k_results(1)
        return top[0] if top else None

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def promote_best_to(self, best: TrialResult, destination: Path) -> None:
        """Copy the best trial's output directory to *destination*.

        Copies the trial output files (CSV + JSON) into *destination* and
        writes ``optimizer_results.json`` with the full results summary.
        """
        src = self.work_dir / f'trial_{best.trial_id:03d}'
        if src.exists():
            destination.mkdir(parents=True, exist_ok=True)
            for item in src.iterdir():
                dest_item = destination / item.name
                if item.is_dir():
                    if dest_item.exists():
                        shutil.rmtree(dest_item)
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)

        self._write_optimizer_results(best, destination)

    def _write_optimizer_results(self, best: TrialResult, destination: Path) -> None:
        """Write ``optimizer_results.json`` to *destination*."""
        all_results = [
            {
                'trial_id': r.trial_id,
                'score': r.score,
                'success': r.success,
                'wall_time': r.wall_time,
                'metrics': {
                    'completion_rate': r.metrics.get('completion_rate', 0.0),
                    'throughput_rate_per_hour': r.metrics.get('throughput_rate_per_hour', 0.0),
                    'workshop_utilization': r.metrics.get('workshop_utilization', 0.0),
                },
                'params': {k: str(v) for k, v in r.params.items()},
            }
            for r in self.sorted_results()
        ]

        summary = {
            'best_trial_id': best.trial_id,
            'best_score': best.score,
            'best_params': {k: str(v) for k, v in best.params.items()},
            'best_metrics': {
                'completion_rate': best.metrics.get('completion_rate', 0.0),
                'throughput_rate_per_hour': best.metrics.get('throughput_rate_per_hour', 0.0),
                'workshop_utilization': best.metrics.get('workshop_utilization', 0.0),
            },
            'n_trials': len(self._results),
            'n_successful': sum(1 for r in self._results if r.success),
            'all_trials': all_results,
        }

        with open(destination / 'optimizer_results.json', 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _suppress_logging() -> Generator[None]:
    """Temporarily raise the root logger level to CRITICAL for one trial."""
    root = logging.getLogger()
    saved_level = root.level
    root.setLevel(logging.CRITICAL)
    try:
        yield
    finally:
        root.setLevel(saved_level)


def _read_summary_metrics(output_dir: Path) -> dict[str, Any]:
    """Read ``summary_metrics.json`` from *output_dir*; return ``{}`` on failure."""
    path = output_dir / 'summary_metrics.json'
    if not path.exists():
        return {}
    with open(path, encoding='utf-8') as fh:
        data: dict[str, Any] = json.load(fh)
    return data
