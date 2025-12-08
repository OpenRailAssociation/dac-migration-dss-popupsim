"""Retrofit request parameter object."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from MVP.workshop_operations.domain.entities.wagon import Wagon


@dataclass
class RetrofitRequest:
    """Groups parameters for wagon retrofit processing."""

    wagon: Wagon
    workshop_resource: Any
    track_id: str
    process_time: timedelta
    workshop_capacity_manager: Any
    metrics: Any
