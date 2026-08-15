"""Windows mouse manipulation with DPI awareness and safety limits."""

import asyncio
import ctypes
import math
import sys
import time
from typing import Optional, Tuple
from src.infrastructure.logger import get_logger

logger = get_logger("mouse")


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class WindowsMouseController:
    """Provides subtle, safe cursor drift and temporary freeze effects."""

    def __init__(self):
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None

    def get_cursor_pos(self) -> Tuple[int, int]:
        if not self._user32:
            return (0, 0)
        pt = POINT()
        self._user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def set_cursor_pos(self, x: int, y: int) -> bool:
        if not self._user32:
            return False
        return bool(self._user32.SetCursorPos(int(x), int(y)))

    async def drift(self, intensity: float = 0.1, duration_ms: int = 500) -> None:
        """Apply subtle sinusoidal mouse drift over duration."""
        if not self._user32:
            return

        start_x, start_y = self.get_cursor_pos()
        duration_sec = min(3.0, max(0.1, duration_ms / 1000.0))
        amplitude = max(5, min(80, int(intensity * 100)))

        start_time = time.time()
        step_interval = 0.02  # 50 Hz updates

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration_sec:
                break

            progress = elapsed / duration_sec
            offset_x = int(math.sin(progress * math.pi * 2) * amplitude)
            offset_y = int(math.cos(progress * math.pi) * (amplitude * 0.5))

            current_x, current_y = self.get_cursor_pos()
            self.set_cursor_pos(current_x + offset_x, current_y + offset_y)
            await asyncio.sleep(step_interval)

    async def freeze(self, duration_ms: int = 1000) -> None:
        """Briefly lock cursor to current position (max 3 seconds safety bound)."""
        if not self._user32:
            return

        cur_x, cur_y = self.get_cursor_pos()
        rect = RECT(cur_x, cur_y, cur_x + 1, cur_y + 1)
        self._user32.ClipCursor(ctypes.byref(rect))

        freeze_sec = min(3.0, max(0.1, duration_ms / 1000.0))
        try:
            await asyncio.sleep(freeze_sec)
        finally:
            # Release cursor clip
            self._user32.ClipCursor(None)
