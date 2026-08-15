"""Platform abstraction interfaces for SENTIENT_OS v2."""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseFileScanner(ABC):
    @abstractmethod
    def scan_safe_files(self) -> List[str]:
        """Scan and return a list of safe user file/folder names."""
        pass


class BaseWindowInfo(ABC):
    @abstractmethod
    def get_active_window_title(self) -> Optional[str]:
        """Get the title of the currently focused active window."""
        pass

    @abstractmethod
    def is_streamer_active(self) -> bool:
        """Check if any streaming or recording software (OBS, Discord) is active."""
        pass
