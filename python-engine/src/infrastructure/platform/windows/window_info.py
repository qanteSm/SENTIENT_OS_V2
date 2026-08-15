"""Windows active window title reader and streamer detection."""

import ctypes
import sys
from typing import Optional
import psutil
from src.infrastructure.platform.common import BaseWindowInfo

STREAMER_PROCESSES = {
    "obs64.exe",
    "obs32.exe",
    "streamlabs.exe",
    "xsplit.exe",
    "discord.exe",
}


class WindowsWindowInfo(BaseWindowInfo):
    """Retrieves foreground window information and checks streamer mode status."""

    def get_active_window_title(self) -> Optional[str]:
        """Read the title text of the currently focused window on Windows."""
        if sys.platform != "win32":
            return None

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return None

            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()
            return title if title else None
        except Exception:
            return None

    def is_streamer_active(self) -> bool:
        """Detect if broadcasting or streaming applications are running."""
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name")
                if name and name.lower() in STREAMER_PROCESSES:
                    return True
        except Exception:
            pass
        return False
