"""Windows screen brightness controller with minimum safety bounds."""

import subprocess
import sys
from typing import Optional
from src.infrastructure.logger import get_logger

logger = get_logger("brightness")


class WindowsBrightnessManager:
    """Adjusts display brightness safely and restores on exit."""

    def __init__(self):
        self._original_brightness: Optional[int] = None
        self.save_original()

    def save_original(self) -> Optional[int]:
        """Query current brightness percentage."""
        if sys.platform != "win32":
            return None

        cmd = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness"
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", cmd],
                timeout=2,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            ).strip()
            if out.isdigit():
                self._original_brightness = int(out)
                logger.info(f"Original brightness saved: {self._original_brightness}%")
                return self._original_brightness
        except Exception:
            pass
        return None

    def set_brightness(self, target_percent: int) -> bool:
        """Set brightness percentage (safety bounded between 20% and 100%)."""
        if sys.platform != "win32":
            return False

        safe_percent = max(20, min(100, int(target_percent)))
        cmd = f"(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1, {safe_percent})"
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                timeout=2,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            logger.info(f"Brightness adjusted to {safe_percent}%")
            return True
        except Exception as e:
            logger.debug(f"Failed to set brightness: {e}")
            return False

    def restore(self) -> bool:
        """Restore original brightness."""
        if self._original_brightness is not None:
            return self.set_brightness(self._original_brightness)
        return False
