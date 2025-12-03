"""Async metrics collection queue for performance optimization."""

import asyncio
from collections import deque
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MetricsQueue:  # pylint: disable=too-few-public-methods
    """Async queue for collecting metrics without blocking simulation."""

    def __init__(self, max_size: int = 1000) -> None:
        self.queue: deque = deque(maxlen=max_size)
        self._processing = False

    async def collect_context_metrics_async(self, contexts: list[tuple[str, Any, str]]) -> dict[str, dict[str, Any]]:
        """Collect metrics from multiple contexts asynchronously."""
        tasks = []

        for context_name, context, method_name in contexts:
            if context:
                task = asyncio.create_task(self._collect_single_context(context_name, context, method_name))
                tasks.append(task)

        if not tasks:
            return {}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results, filtering out exceptions
        combined_metrics = {}
        for result in results:
            if isinstance(result, dict):
                combined_metrics.update(result)
            elif isinstance(result, Exception):
                logger.warning('Context metrics collection failed: %s', result)

        return combined_metrics

    async def _collect_single_context(
        self, context_name: str, context: Any, method_name: str
    ) -> dict[str, dict[str, Any]]:
        """Collect metrics from single context."""
        try:
            loop = asyncio.get_event_loop()
            method = getattr(context, method_name)
            metrics = await loop.run_in_executor(None, method)
            return {context_name: metrics}
        except (AttributeError, TypeError, RuntimeError, ValueError) as e:
            logger.warning('Failed to collect %s metrics: %s', context_name, e)
            return {context_name: {}}
