"""Windows-specific platform integrations."""

from .brightness import WindowsBrightnessManager
from .file_scanner import WindowsFileScanner
from .keyboard import KeyboardPanicDetector
from .mouse import WindowsMouseController
from .notifications import NotificationManager
from .wallpaper import WindowsWallpaperManager
from .window_info import WindowsWindowInfo

__all__ = [
    "WindowsBrightnessManager",
    "WindowsFileScanner",
    "KeyboardPanicDetector",
    "WindowsMouseController",
    "NotificationManager",
    "WindowsWallpaperManager",
    "WindowsWindowInfo",
]
