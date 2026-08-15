"""Windows file scanner with privacy protection."""

from typing import List, Optional
from src.infrastructure.platform.common import BaseFileScanner
from src.infrastructure.privacy_filter import PrivacyFilter


class WindowsFileScanner(BaseFileScanner):
    """Safely gathers clean user folder/file names using PrivacyFilter."""

    def __init__(self, privacy_filter: Optional[PrivacyFilter] = None):
        self.privacy_filter = privacy_filter or PrivacyFilter()

    def scan_safe_files(self) -> List[str]:
        """Perform 1-level scan of user whitelist folders and return clean names."""
        return self.privacy_filter.scan_whitelist_locations()
