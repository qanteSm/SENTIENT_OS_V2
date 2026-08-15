"""Windows-specific platform integrations."""

from .file_scanner import WindowsFileScanner
from .window_info import WindowsWindowInfo

__all__ = ["WindowsFileScanner", "WindowsWindowInfo"]
