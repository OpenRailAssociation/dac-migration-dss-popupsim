"""Simulation execution harness for the optimizer (single and parallel runs)."""

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import contextlib
import io
import logging
import os
from pathlib import Path
import shutil
import sys
import tempfile

from contexts.configuration.domain.models.scenario import Scenario
from main import run
from optimizer.summary_model import SummaryMetrics
from optimizer.util import score

try:
    from tqdm import tqdm

    _HAS_TQDM = True
except ImportError:
    _HAS_TQDM = False

type ScenarioResult = tuple[SummaryMetrics, float, Scenario]
type ScenarioTask = tuple[Path, Scenario, float, float]


def run_simulation(
    scenario_dir: Path, scenario: Scenario | None = None, weight_completion: float = 0.9, weight_loco: float = -0.1
) -> ScenarioResult:
    """Run a single simulation and return its summary, score and resolved scenario."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output_tmp = tmp_path / 'output'

        if scenario is not None:
            scenario_path = tmp_path / 'scenario'
            shutil.copytree(scenario_dir, scenario_path)
            exclude_fields = {'tracks', 'workshops', 'locomotives', 'trains', 'topology', 'process_times'}
            (scenario_path / 'scenario.json').write_text(
                scenario.model_dump_json(indent=2, exclude=exclude_fields), encoding='utf-8'
            )
        else:
            scenario_path = scenario_dir

        sink = io.StringIO()
        logging.disable(logging.CRITICAL)
        try:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                run(scenario_path=scenario_path, output_path=output_tmp, verbose=False)
        except SystemExit as exc:
            if exc.code != 0:
                raise RuntimeError(f'Simulation failed for scenario in {scenario_path}') from exc
        finally:
            logging.disable(logging.NOTSET)

        summary_file = output_tmp / 'summary_metrics.json'
        if not summary_file.exists():
            raise RuntimeError(f'summary_metrics.json not found in {output_tmp}')

        summary = SummaryMetrics.model_validate_json(summary_file.read_text(encoding='utf-8'))

        if scenario is None:
            scenario = Scenario.model_validate_json((scenario_path / 'scenario.json').read_text(encoding='utf-8'))

        return (summary, score(summary, weight_completion, weight_loco), scenario)


def _run_single_scenario(args: ScenarioTask) -> ScenarioResult:
    """Worker entry point: ensure the src dir is importable, then run one simulation."""
    # Worker subprocesses start with a fresh interpreter, so the backend src
    # directory must be re-added to sys.path before optimizer imports resolve.
    src_dir = str(Path(__file__).resolve().parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    scenario_dir, scenario, weight_completion, weight_loco = args
    return run_simulation(scenario_dir, scenario, weight_completion, weight_loco)


def run_parallel(
    scenario_dir: Path,
    scenarios: list[Scenario],
    weight_completion: float = 0.9,
    weight_loco: float = -0.1,
    max_workers: int | None = None,
) -> list[ScenarioResult | None]:
    """Run simulations for many scenarios in parallel, preserving input order."""
    workers = max_workers if max_workers and max_workers > 0 else (os.cpu_count() or 1)
    tasks: list[ScenarioTask] = [(scenario_dir, scenario, weight_completion, weight_loco) for scenario in scenarios]
    results: list[ScenarioResult | None] = [None] * len(scenarios)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_run_single_scenario, task): i for i, task in enumerate(tasks)}
        completed = as_completed(futures)
        if _HAS_TQDM:
            completed = tqdm(completed, total=len(futures), desc='Running scenarios in parallel')
        for future in completed:
            results[futures[future]] = future.result()

    return results
