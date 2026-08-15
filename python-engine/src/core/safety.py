"""Safety subsystem for SENTIENT_OS v2.

Provides isolated kill switch, resource guard, and orphan file cleanups.
"""

import asyncio
import ctypes
import glob
import os
import subprocess
import sys
import threading
from typing import Callable, Optional
import psutil

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("safety")


def cleanup_tts_temp_files(temp_dir: str = "temp/") -> int:
    """Clean orphan TTS audio files synchronously."""
    pattern = os.path.join(temp_dir, "tts_*.mp3")
    orphans = glob.glob(pattern)
    cleaned = 0
    for f in orphans:
        try:
            os.remove(f)
            cleaned += 1
        except OSError:
            pass

    if cleaned > 0:
        logger.info(f"Cleaned {cleaned} orphan TTS audio files")
    return cleaned


class IsolatedKillSwitch:
    """
    Dedicated native thread listening for Ctrl+Shift+Q emergency abort hotkey.
    Completely decoupled from asyncio event loops and IPC locks.
    """

    HOTKEY_ID = 1
    MOD_CTRL = 0x0002
    MOD_SHIFT = 0x0004
    VK_Q = 0x51
    WM_HOTKEY = 0x0312

    def __init__(
        self,
        restore_callback: Optional[Callable[[], None]] = None,
        electron_pid: Optional[int] = None,
        temp_dir: str = "temp/",
    ):
        self._restore_callback = restore_callback
        self._electron_pid = electron_pid
        self._temp_dir = temp_dir
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def set_electron_pid(self, pid: int) -> None:
        """Update Electron PID once received from handshake."""
        self._electron_pid = pid

    def start(self) -> None:
        """Start listener thread if on Windows platform."""
        if sys.platform != "win32":
            logger.warning("IsolatedKillSwitch Win32 hotkey is only active on Windows.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True, name="KillSwitchThread")
        self._thread.start()
        logger.info("Isolated KillSwitch registered (Ctrl+Shift+Q)")

    def _listen(self) -> None:
        """Native Windows message pump for RegisterHotKey."""
        user32 = ctypes.windll.user32
        registered = user32.RegisterHotKey(
            None, self.HOTKEY_ID, self.MOD_CTRL | self.MOD_SHIFT, self.VK_Q
        )
        if not registered:
            logger.error("Failed to register Windows HotKey Ctrl+Shift+Q")
            return

        msg = ctypes.wintypes.MSG()
        try:
            while self._running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == self.WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                    logger.critical("[KILL SWITCH] Emergency abort triggered by user hotkey!")
                    self._emergency_shutdown()
                    break
        finally:
            user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def _emergency_shutdown(self) -> None:
        """Execute instantaneous cleanup and kill processes."""
        # 1. Execute restore callback if provided
        if self._restore_callback:
            try:
                self._restore_callback()
            except Exception as e:
                logger.error(f"Error during emergency restore: {e}")

        # 2. Synchronous file cleanup
        cleanup_tts_temp_files(self._temp_dir)

        # 3. Kill Electron process tree if PID exists
        if self._electron_pid:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self._electron_pid)],
                    capture_output=True,
                    timeout=3,
                )
            except Exception:
                pass

        # 4. Immediate exit
        os._exit(0)


class ResourceGuard:
    """Monitors system CPU and RAM usage and triggers safety shutdowns when thresholds are exceeded."""

    def __init__(
        self,
        event_bus: EventBus,
        cpu_warning: int = 80,
        cpu_critical: int = 90,
        ram_warning_mb: int = 500,
        ram_critical_mb: int = 750,
        check_interval: float = 5.0,
    ):
        self.event_bus = event_bus
        self.cpu_warning = cpu_warning
        self.cpu_critical = cpu_critical
        self.ram_warning_mb = ram_warning_mb
        self.ram_critical_mb = ram_critical_mb
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._is_running = False

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._is_running = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("ResourceGuard started")

    async def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("ResourceGuard stopped")

    async def _monitor_loop(self) -> None:
        process = psutil.Process()
        while self._is_running:
            try:
                await asyncio.sleep(self.check_interval)
                cpu = psutil.cpu_percent(interval=None)
                ram_mb = process.memory_info().rss / (1024 * 1024)

                if cpu >= self.cpu_critical:
                    logger.critical(f"CPU usage critical: {cpu:.1f}% (threshold {self.cpu_critical}%)")
                    await self.event_bus.publish(
                        "safety.shutdown",
                        reason="CPU overload",
                        metric="cpu",
                        value=cpu,
                    )
                    break
                elif cpu >= self.cpu_warning:
                    logger.warning(f"CPU usage warning: {cpu:.1f}%")

                if ram_mb >= self.ram_critical_mb:
                    logger.critical(f"RAM usage critical: {ram_mb:.1f}MB (threshold {self.ram_critical_mb}MB)")
                    await self.event_bus.publish(
                        "safety.shutdown",
                        reason="RAM overload",
                        metric="ram",
                        value=ram_mb,
                    )
                    break
                elif ram_mb >= self.ram_warning_mb:
                    logger.warning(f"RAM usage high: {ram_mb:.1f}MB")
                    await self.event_bus.publish("safety.memory_pressure", current_mb=ram_mb)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ResourceGuard check: {e}")
