"""Windows desktop wallpaper backup and temporary modification."""

import ctypes
import os
import sys
from typing import Optional
from src.infrastructure.logger import get_logger

logger = get_logger("wallpaper")

SPI_GETDESKWALLPAPER = 0x0073
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02


class WindowsWallpaperManager:
    """Safely saves original desktop wallpaper and restores it upon shutdown."""

    def __init__(self):
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self._original_wallpaper: Optional[str] = None
        self.save_original()

    def save_original(self) -> Optional[str]:
        if not self._user32:
            return None

        buff = ctypes.create_unicode_buffer(512)
        success = self._user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 512, buff, 0)
        if success and buff.value:
            self._original_wallpaper = buff.value
            logger.info(f"Original wallpaper saved: '{self._original_wallpaper}'")
            return self._original_wallpaper
        return None

    def set_wallpaper(self, image_path: str) -> bool:
        """Set wallpaper to a specific image file."""
        if not self._user32 or not os.path.exists(image_path):
            return False

        abs_path = os.path.abspath(image_path)
        success = self._user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        if success:
            logger.info(f"Wallpaper changed to '{abs_path}'")
        return bool(success)

    def restore(self) -> bool:
        """Restore original desktop wallpaper."""
        if not self._user32 or not self._original_wallpaper:
            return False

        success = self._user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            self._original_wallpaper,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
        )
        if success:
            logger.info("Original wallpaper restored successfully")
        return bool(success)
