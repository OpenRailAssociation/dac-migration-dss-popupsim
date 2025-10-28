import sys
from pathlib import Path
from typing import Any, Generator, Optional

import pytest

# Ensure src is on path for imports when tests are executed from repository root
ROOT: Path = Path(__file__).resolve().parents[4]  # repo root
SRC: Path = ROOT / 'popupsim' / 'backend' / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.simulation.sim_adapter import SimPyAdapter


class FakeProcess:
    def __init__(self, gen: Generator[Any, None, Any]) -> None:
        self.gen: Generator[Any, None, Any] = gen


class FakeEnv:
    def __init__(self) -> None:
        self.now: float = 0.0
        self.last_timeout: Optional[float] = None
        self.run_called_with: Optional[float] = None
        self.last_process_arg: Optional[Generator[Any, None, Any]] = None

    def timeout(self, duration: float) -> tuple[str, float]:
        self.last_timeout = duration
        return ('timeout', duration)

    def run(self, until: Optional[float] = None) -> tuple[str, Optional[float]]:
        self.run_called_with = until
        return ('ran', until)

    def process(self, gen: Generator[Any, None, Any]) -> FakeProcess:
        self.last_process_arg = gen
        return FakeProcess(gen)


class FakeSimpyModule:
    Environment = FakeEnv  # type: ignore


@pytest.mark.unit
def test_simpy_adapter_create_and_basic_delegation() -> None:
    # Inject fake simpy module so create_simpy_adapter does not require real simpy
    sys.modules['simpy'] = FakeSimpyModule  # type: ignore
    try:
        adapter: SimPyAdapter = SimPyAdapter.create_simpy_adapter()
        # type checks: adapter should expose current_time/delay/run
        assert isinstance(adapter, SimPyAdapter)
        # current_time delegates to env.now
        assert isinstance(adapter.current_time(), float)
        # delay delegates to env.timeout
        timeout_result = adapter.delay(5.0)
        assert timeout_result == ('timeout', 5.0)
        # run delegates to env.run
        run_result = adapter.run(10.0)
        assert run_result == ('ran', 10.0)
    finally:
        # Clean up injected module to avoid leaking into other tests
        del sys.modules['simpy']


@pytest.mark.unit
def test_run_process_with_prebuilt_generator_object() -> None:
    # Prepare fake simpy and adapter
    sys.modules['simpy'] = FakeSimpyModule  # type: ignore
    try:
        adapter: SimPyAdapter = SimPyAdapter.create_simpy_adapter()

        # create a generator object (pre-built)
        def gen_func() -> Generator[int, None, None]:
            yield 1

        gen_obj: Generator[int, None, None] = gen_func()
        proc = adapter.run_process(gen_obj)  # should schedule the same generator object
        assert isinstance(proc, FakeProcess)

    finally:
        del sys.modules['simpy']


@pytest.mark.unit
def test_run_process_with_normal_callable_wrapped_in_generator() -> None:
    # Prepare fake simpy and adapter
    sys.modules['simpy'] = FakeSimpyModule  # type: ignore
    try:
        adapter: SimPyAdapter = SimPyAdapter.create_simpy_adapter()

        def normal_callable(a: int, b: int) -> None:
            # side effect to observe when wrapper generator is executed
            assert a == 7
            assert b == 8

        proc = adapter.run_process(normal_callable, 7, 8)
        assert isinstance(proc, FakeProcess)
    finally:
        del sys.modules['simpy']
