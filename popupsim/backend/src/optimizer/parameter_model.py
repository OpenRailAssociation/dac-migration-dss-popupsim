from abc import ABC, abstractmethod
import random
from typing import Any, Generic, Iterator, TypeVar
from dataclasses import dataclass
from itertools import product

T = TypeVar("T")

class Parameter(ABC, Generic[T]):

    @abstractmethod
    def iter_values(self) -> Iterator[T]:
        """Enumerate all discrete values. Raises if purely continuous."""
        ...

    @abstractmethod
    def sample_value(self, rng: random.Random) -> T:
        """Draw one value uniformly at random."""
        ...

    @abstractmethod
    def size(self) -> int:
        """Number of distinct values."""
        ...

@dataclass(frozen=True)
class DiscreteParameter(Parameter[T]):

    values: tuple[T, ...]

    def iter_values(self) -> Iterator[T]:
        yield from self.values

    def sample_value(self, rng: random.Random) -> T:
        return rng.choice(self.values)

    def size(self) -> int:
        return len(self.values)

@dataclass(frozen=True)
class ContinuousParameter(Parameter[float]):
    low: float
    high: float
    step_size: float

    def iter_values(self) -> Iterator[float]:
        size = self.size()
        if size is None:
            raise NotImplementedError("ContinuousParameter without steps cannot be enumerated.")
        for i in range(size):
            yield self.low + i * self.step_size

    def sample_value(self, rng: random.Random) -> float:
        return rng.uniform(self.low, self.high)

    def size(self) -> int:
        return int((self.high - self.low) / self.step_size) + 1
    
def _make_canonical(val: Any) -> Any:
    """Recursively convert unhashable types (dicts, lists) into hashable counterparts (tuples)."""
    if isinstance(val, dict):
        return tuple(sorted((k, _make_canonical(v)) for k, v in val.items()))
    elif isinstance(val, (list, tuple)):
        return tuple(_make_canonical(x) for x in val)
    return val


def _safe_sort_key(val: Any) -> Any:
    """Generate a sort key for canonicalized values to ensure deterministic sorting of mixed types."""
    if val is None:
        return (0, "")
    if isinstance(val, (bool, int, float)):
        return (1, float(val))
    if isinstance(val, str):
        return (2, val)
    if isinstance(val, tuple):
        return (3, tuple(_safe_sort_key(x) for x in val))
    if hasattr(val, "value"):
        return (4, _safe_sort_key(val.value))
    return (5, str(val))


@dataclass(frozen=True)
class ListParameter(Parameter[list[Any]]):
    slots: tuple[Parameter[Any], ...]

    def iter_values(self) -> Iterator[list[Any]]:
        # Pre-canonicalize all values for each slot to avoid repeating in the Cartesian product
        canonical_slots = []
        for slot in self.slots:
            slot_vals = list(slot.iter_values())
            canonical_vals = []
            for v in slot_vals:
                c = _make_canonical(v)
                k = _safe_sort_key(c)
                canonical_vals.append((c, k, v))
            canonical_slots.append(canonical_vals)

        seen = set()
        for combo in product(*canonical_slots):
            # Filter out None values
            filtered = [item for item in combo if item[0] is not None]
            # Sort by safe sort key to treat different orders as equivalent
            filtered.sort(key=lambda item: item[1])

            canonical_combo = tuple(item[0] for item in filtered)
            if canonical_combo not in seen:
                seen.add(canonical_combo)
                yield [item[2] for item in filtered]

    def sample_value(self, rng: random.Random) -> list[Any]:
        combo = [slot.sample_value(rng) for slot in self.slots]
        canonical_elements = [(_make_canonical(x), x) for x in combo if x is not None]
        canonical_elements.sort(key=lambda item: _safe_sort_key(item[0]))
        return [item[1] for item in canonical_elements]

    def size(self) -> int:
        return sum(1 for _ in self.iter_values())

    @classmethod
    def repeat(cls, slot: Parameter[Any], max_count: int) -> "ListParameter":
        return cls(slots=tuple(slot for _ in range(max_count)))

    
@dataclass
class GroupParameter(Parameter[dict[str, Any] | None]):
    params: dict[str, Parameter[Any]]
    optional: bool = True

    def _sub_size(self) -> int:
        total = 1
        for p in self.params.values():
            s = p.size()
            total *= s
        return total

    def iter_values(self) -> Iterator[dict[str, Any] | None]:
        if self.optional:
            yield None
        keys = list(self.params.keys())
        for combo in product(*(self.params[k].iter_values() for k in keys)):
            yield dict(zip(keys, combo))

    def sample_value(self, rng: random.Random) -> dict[str, Any] | None:
        if self.optional and rng.random() < 1.0 / (self._sub_size() + 1):
            return None
        return {k: p.sample_value(rng) for k, p in self.params.items()}

    def size(self) -> int:
        return sum(1 for _ in self.iter_values())
