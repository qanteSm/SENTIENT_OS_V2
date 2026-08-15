"""Keyboard monitoring for panic detection (ESC spam, Alt+F4)."""

import time
from typing import Callable, List, Optional
from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("keyboard")


class KeyboardPanicDetector:
    """Tracks keypress intervals for panic triggers (ESC spam, Alt+F4 attempts)."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._esc_timestamps: List[float] = []
        self._alt_f4_timestamps: List[float] = []

    async def record_esc_pressed(self) -> None:
        now = time.time()
        self._esc_timestamps.append(now)
        # Keep only timestamps in last 2 seconds
        self._esc_timestamps = [t for t in self._esc_timestamps if now - t <= 2.0]

        if len(self._esc_timestamps) >= 5:
            logger.warning("[PANIC DETECTED] 5+ ESC keys pressed in 2 seconds.")
            await self.event_bus.publish("safety.panic_detected", trigger="esc_spam")

    async def record_alt_f4_attempt(self) -> None:
        now = time.time()
        self._alt_f4_timestamps.append(now)
        self._alt_f4_timestamps = [t for t in self._alt_f4_timestamps if now - t <= 5.0]

        if len(self._alt_f4_timestamps) >= 3:
            logger.warning("[PANIC DETECTED] 3+ Alt+F4 attempts in 5 seconds.")
            await self.event_bus.publish("safety.panic_detected", trigger="alt_f4_spam")
