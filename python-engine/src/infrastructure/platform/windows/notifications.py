"""Windows native notifications helper."""

from typing import Any, Optional
from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("notifications")


class NotificationManager:
    """Dispatches fake Windows toast notification events to Electron overlay."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def show_notification(
        self, title: str, body: str, icon_type: str = "warning", duration_ms: int = 4000
    ) -> None:
        """Publish fake notification event for realistic rendering in Electron overlay."""
        logger.info(f"Showing fake notification: '{title}' - '{body}'")
        await self.event_bus.publish(
            "effect",
            payload={
                "category": "system",
                "name": "fake_notification",
                "params": {
                    "title": title,
                    "body": body,
                    "icon_type": icon_type,
                    "duration_ms": duration_ms,
                },
                "priority": "normal",
            },
        )
