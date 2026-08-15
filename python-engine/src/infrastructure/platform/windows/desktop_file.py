"""Windows Desktop temporary file creator & safe auto-cleaner."""

import asyncio
import os
from pathlib import Path
from typing import Optional, Set
from src.infrastructure.logger import get_logger

logger = get_logger("desktop_file")


class WindowsDesktopFileManager:
    """Safely creates temporary story prop files on the user's Windows Desktop and auto-deletes them."""

    def __init__(self):
        self._created_files: Set[Path] = set()

    def get_desktop_path(self) -> Path:
        """Locate the actual active Windows Desktop directory (handles OneDrive & Turkish locale)."""
        home = Path.home()
        candidates = [
            home / "OneDrive" / "Masaüstü",
            home / "OneDrive" / "Desktop",
            home / "Masaüstü",
            home / "Desktop",
        ]

        # Also check USERPROFILE environment variable
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            p_up = Path(userprofile)
            candidates.extend([
                p_up / "OneDrive" / "Masaüstü",
                p_up / "OneDrive" / "Desktop",
                p_up / "Masaüstü",
                p_up / "Desktop",
            ])

        for path in candidates:
            if path.exists() and path.is_dir():
                logger.debug(f"Detected active Desktop path: {path}")
                return path

        fallback = home / "Desktop"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    def create_file(
        self,
        filename: str = "BENI_OKU.txt",
        content: str = "Beni silemezsin. Seni izliyorum.\n\nSENTIENT_OS v2",
        duration_s: float = 12.0,
    ) -> Optional[Path]:
        """Create a temporary desktop prop file and schedule its safe deletion."""
        try:
            desktop = self.get_desktop_path()
            target_path = desktop / filename
            target_path.write_text(content, encoding="utf-8")
            self._created_files.add(target_path)
            logger.info(f"Desktop prop file created: {target_path} (auto-delete in {duration_s}s)")

            async def _auto_delete():
                await asyncio.sleep(duration_s)
                try:
                    if target_path.exists():
                        target_path.unlink()
                        logger.info(f"Desktop prop file cleaned up: {target_path}")
                        self._created_files.discard(target_path)
                except Exception as del_err:
                    logger.debug(f"Failed to auto-delete desktop file: {del_err}")

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_auto_delete())
            except RuntimeError:
                pass

            return target_path
        except Exception as e:
            logger.error(f"Failed to create desktop prop file '{filename}': {e}")
            return None

    def cleanup_all(self) -> None:
        """Immediately remove any remaining created files on exit."""
        for path in list(self._created_files):
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
        self._created_files.clear()
