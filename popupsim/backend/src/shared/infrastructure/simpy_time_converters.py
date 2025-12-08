"""Converters between domain time types and SimPy float times.

SimPy is unit-agnostic - it just counts 'ticks'. We define what a tick means.
This module provides the SINGLE SOURCE OF TRUTH for time unit conversions.
"""

from datetime import datetime
from datetime import timedelta
from enum import Enum


class SimulationTimeUnit(Enum):
    """Simulation time unit for SimPy ticks."""

    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'


# Global configuration - SINGLE SOURCE OF TRUTH
# Change this to change simulation time unit everywhere
SIMULATION_TIME_UNIT = SimulationTimeUnit.MINUTES


def timedelta_to_sim_ticks(td: timedelta) -> float:
    """Convert timedelta to SimPy ticks based on configured unit.

    This is the ONLY function that should convert timedelta to float for SimPy.
    All SimPy delays should use this function.

    Parameters
    ----------
    td : timedelta
        Duration to convert

    Returns
    -------
    float
        Duration in SimPy ticks (unit defined by SIMULATION_TIME_UNIT)
    """
    total_seconds = td.total_seconds()

    if SIMULATION_TIME_UNIT == SimulationTimeUnit.SECONDS:
        return total_seconds
    if SIMULATION_TIME_UNIT == SimulationTimeUnit.MINUTES:
        return total_seconds / 60.0
    if SIMULATION_TIME_UNIT == SimulationTimeUnit.HOURS:
        return total_seconds / 3600.0
    msg = f'Unknown time unit: {SIMULATION_TIME_UNIT}'
    raise ValueError(msg)


def sim_ticks_to_timedelta(ticks: float) -> timedelta:
    """Convert SimPy ticks to timedelta based on configured unit.

    This is the ONLY function that should convert float to timedelta from SimPy.

    Parameters
    ----------
    ticks : float
        SimPy simulation time in ticks

    Returns
    -------
    timedelta
        Duration as timedelta
    """
    if SIMULATION_TIME_UNIT == SimulationTimeUnit.SECONDS:
        return timedelta(seconds=ticks)
    if SIMULATION_TIME_UNIT == SimulationTimeUnit.MINUTES:
        return timedelta(minutes=ticks)
    if SIMULATION_TIME_UNIT == SimulationTimeUnit.HOURS:
        return timedelta(hours=ticks)
    msg = f'Unknown time unit: {SIMULATION_TIME_UNIT}'
    raise ValueError(msg)


def datetime_to_sim_delay(target_time: datetime, current_time: datetime) -> float:
    """Calculate SimPy delay in ticks between two datetimes.

    Parameters
    ----------
    target_time : datetime
        Target time (must be timezone-aware)
    current_time : datetime
        Current time (must be timezone-aware)

    Returns
    -------
    float
        Delay in SimPy ticks
    """
    if target_time.tzinfo is None or current_time.tzinfo is None:
        msg = 'Both datetimes must be timezone-aware'
        raise ValueError(msg)

    delay = target_time - current_time
    return timedelta_to_sim_ticks(delay)


def get_simulation_time_unit_name() -> str:
    """Get human-readable name of current simulation time unit."""
    return SIMULATION_TIME_UNIT.value


# Backward compatibility aliases
def timedelta_to_simpy_minutes(td: timedelta) -> float:
    """Convert timedelta to SimPy minutes (deprecated, use timedelta_to_sim_ticks)."""
    return timedelta_to_sim_ticks(td)


def simpy_minutes_to_timedelta(minutes: float) -> timedelta:
    """Convert SimPy minutes to timedelta (deprecated, use sim_ticks_to_timedelta)."""
    return sim_ticks_to_timedelta(minutes)


def datetime_to_simpy_delay(target_time: datetime, current_time: datetime) -> float:
    """Calculate SimPy delay from datetimes (deprecated, use datetime_to_sim_delay)."""
    return datetime_to_sim_delay(target_time, current_time)
