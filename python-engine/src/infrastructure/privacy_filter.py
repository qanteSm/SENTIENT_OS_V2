"""Privacy filter and safe file scanner for SENTIENT_OS v2.

Ensures sensitive user files are NEVER exposed or inspected.
Extracts only benign file/folder names (never contents or full paths).
"""

import fnmatch
import os
from pathlib import Path
from typing import List, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("privacy_filter")

# Blacklisted file/folder patterns (case-insensitive)
BLACKLISTED_PATTERNS = [
    # Security files
    ".env",
    ".env.*",
    ".env.local",
    ".env.production",
    ".ssh",
    ".ssh*",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
    "*.pem",
    "*.key",
    "*.crt",
    "*.pfx",
    "*.kdbx",
    "*.keystore",
    "*.jks",
    # Passwords / credentials / tokens
    "*password*",
    "*parola*",
    "*sifre*",
    "*şifre*",
    "*secret*",
    "*credential*",
    "*token*",
    "*api_key*",
    "*apikey*",
    # Browser user data
    "*Chrome*",
    "*Firefox*",
    "*Edge*",
    "*Cookies*",
    "*Login Data*",
    # System / binary files
    "node_modules",
    ".git",
    "__pycache__",
    ".vscode",
    ".idea",
    "*.exe",
    "*.dll",
    "*.sys",
    "*.msi",
    "*.bat",
    "*.cmd",
    "*.ps1",
    "*.vbs",
    "*.lnk",
    "*.ini",
    "Desktop.ini",
    "Thumbs.db",
]

# Standard whitelist folder names
WHITELIST_DIRECTORIES = ["Desktop", "Documents", "Downloads"]


class PrivacyFilter:
    """Filters filenames and scans user directories safely."""

    def __init__(
        self,
        blacklisted_patterns: Optional[List[str]] = None,
        whitelist_directories: Optional[List[str]] = None,
        max_items: int = 30,
    ):
        self.blacklisted_patterns = blacklisted_patterns or list(BLACKLISTED_PATTERNS)
        self.whitelist_directories = whitelist_directories or list(WHITELIST_DIRECTORIES)
        self.max_items = max_items

    def is_blacklisted(self, name_or_path: str) -> bool:
        """Check whether a filename or path matches any blacklisted pattern."""
        basename = os.path.basename(name_or_path).lower()
        path_lower = name_or_path.lower().replace("\\", "/")

        for pattern in self.blacklisted_patterns:
            pat_lower = pattern.lower()
            if fnmatch.fnmatch(basename, pat_lower) or fnmatch.fnmatch(path_lower, f"*{pat_lower}*"):
                return True
        return False

    def filter_names(self, names: List[str]) -> List[str]:
        """Filter a list of filenames or paths, stripping paths and discarding blacklisted items."""
        safe_names: List[str] = []
        for item in names:
            name = os.path.basename(item).strip()
            if not name or name.startswith("."):
                continue
            if not self.is_blacklisted(name):
                if name not in safe_names:
                    safe_names.append(name)
            if len(safe_names) >= self.max_items:
                break
        return safe_names

    def scan_whitelist_locations(self, user_home: Optional[str] = None) -> List[str]:
        """
        Safely inspect whitelist locations on the current system (1 level depth).
        Returns a list of up to `max_items` clean folder/file names without full paths.
        """
        if user_home is None:
            user_home = str(Path.home())

        home_path = Path(user_home)
        discovered_names: List[str] = []

        for target_dir in self.whitelist_directories:
            folder_path = home_path / target_dir
            if not folder_path.exists() or not folder_path.is_dir():
                continue

            try:
                # 1 level depth only
                with os.scandir(folder_path) as entries:
                    for entry in entries:
                        if len(discovered_names) >= self.max_items:
                            break
                        name = entry.name
                        if name.startswith("."):
                            continue
                        if not self.is_blacklisted(name):
                            if name not in discovered_names:
                                discovered_names.append(name)
            except (PermissionError, OSError) as e:
                logger.debug(f"Skipping {folder_path} due to permission/access: {e}")

        logger.info(f"Privacy filter scan complete: {len(discovered_names)} safe items found")
        return discovered_names[: self.max_items]
