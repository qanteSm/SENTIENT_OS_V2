"""Async Publish/Subscribe Event Bus for SENTIENT_OS v2."""

import asyncio
import inspect
from collections import defaultdict
from typing import Any, Callable, Dict, List
from src.infrastructure.logger import get_logger

logger = get_logger("event_bus")


class EventBus:
    """Central asynchronous pub/sub event bus with error isolation."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe a callback to an event type."""
        async with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logger.debug(f"Subscribed callback to '{event_type}'")

    async def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe a callback from an event type."""
        async with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed callback from '{event_type}'")

    async def publish(self, event_type: str, **kwargs: Any) -> None:
        """Publish an event to all subscribers asynchronously with error isolation."""
        async with self._lock:
            # Copy subscriber list to allow modifications during dispatch
            callbacks = list(self._subscribers.get(event_type, []))
            # Also notify wildcard subscribers if any
            wildcards = list(self._subscribers.get("*", []))
            all_callbacks = callbacks + wildcards

        if not all_callbacks:
            return

        tasks = []
        for cb in all_callbacks:
            tasks.append(self._invoke_callback(cb, event_type, kwargs))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _invoke_callback(
        self, callback: Callable, event_type: str, kwargs: dict[str, Any]
    ) -> None:
        """Safely execute a single subscriber callback."""
        try:
            if inspect.iscoroutinefunction(callback):
                await callback(event_type=event_type, **kwargs)
            else:
                # Run synchronous callback in threadpool to prevent event loop blocking
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: callback(event_type=event_type, **kwargs))
        except Exception as e:
            logger.error(
                f"Error in subscriber {getattr(callback, '__name__', repr(callback))} "
                f"for event '{event_type}': {e}",
                exc_info=True,
            )

    def subscriber_count(self, event_type: str) -> int:
        """Return the number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))

    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()
