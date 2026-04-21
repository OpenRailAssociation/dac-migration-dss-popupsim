"""Unified selection strategy for resource allocation.

This module provides a single source of truth for selection strategies
used across all resource types (tracks, workshops, locomotives, etc.).
"""

from enum import StrEnum


class SelectionStrategy(StrEnum):
    """Unified selection strategy for all resources.

    Strategies determine how the system selects between multiple resources
    of the same type when multiple options are available.
    """

    LEAST_OCCUPIED = 'least_occupied'
    """Select resource with most free space/capacity (least utilized)."""

    FIRST_AVAILABLE = 'first_available'
    """Select first resource with sufficient capacity."""

    ROUND_ROBIN = 'round_robin'
    """Cycle through resources sequentially for fair distribution."""

    RANDOM = 'random'
    """Random selection from available resources."""

    BEST_FIT = 'best_fit'
    """Select resource with least available capacity to minimize waste."""

    MOST_AVAILABLE = 'most_available'
    """Select resource with most available capacity."""

    SHORTEST_QUEUE = 'shortest_queue'
    """Select resource with shortest waiting queue."""
