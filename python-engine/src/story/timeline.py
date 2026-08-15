"""Timeline Scheduler and Idle-Aware Pacing Engine for SENTIENT_OS v2."""

import asyncio
import time
from typing import List, Optional
from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger
from src.story.narrative import NarrativePhase
from src.story.scenes.first_contact import FIRST_CONTACT_EVENTS, SceneEvent

logger = get_logger("timeline")

BASE_INTERVAL = 30.0
IDLE_COMPRESSION = 0.4    # If idle > 30s, accelerate pacing by 40% (18s)
ACTIVE_EXTENSION = 1.5    # If active, relax pacing by 50% (45s)


class Timeline:
    """Schedules and dispatches scripted narrative events with dynamic pacing."""

    def __init__(
        self,
        event_bus: EventBus,
        events: Optional[List[SceneEvent]] = None,
        base_interval: float = BASE_INTERVAL,
    ):
        self.event_bus = event_bus
        self.events = events or list(FIRST_CONTACT_EVENTS)
        self.base_interval = base_interval

        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        self._is_idle = False
        self._idle_seconds = 0.0
        self._current_event_idx = 0
        self._phase_start_time: float = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_idle_state(self, is_idle: bool, idle_seconds: float = 0.0) -> None:
        """Update idle state to adjust pacing intervals."""
        self._is_idle = is_idle
        self._idle_seconds = idle_seconds

    def calculate_next_delay(self) -> float:
        """Calculate dynamic delay based on player activity level."""
        if self._is_idle and self._idle_seconds > 30.0:
            return self.base_interval * (1.0 - IDLE_COMPRESSION)
        return self.base_interval * (ACTIVE_EXTENSION if not self._is_idle else 1.0)

    async def start_phase(self, phase: NarrativePhase) -> None:
        """Start scheduler for the given phase."""
        await self.stop()

        if phase == NarrativePhase.FIRST_CONTACT:
            self._is_running = True
            self._current_event_idx = 0
            self._phase_start_time = time.time()
            self._task = asyncio.create_task(self._timeline_loop())
            logger.info("Timeline scheduler started for FIRST_CONTACT")

    async def stop(self) -> None:
        """Stop active timeline scheduler cleanly."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.debug("Timeline scheduler stopped")

    async def _timeline_loop(self) -> None:
        """Loop through scripted events and publish them at calculated intervals."""
        while self._is_running and self._current_event_idx < len(self.events):
            event = self.events[self._current_event_idx]

            # Calculate interval
            delay = self.calculate_next_delay()
            try:
                await asyncio.sleep(min(delay, 10.0))  # Step in chunks to allow fast stopping
            except asyncio.CancelledError:
                break

            if not self._is_running:
                break

            # Dispatch event
            logger.info(f"[Timeline Event {self._current_event_idx + 1}/{len(self.events)}] {event.description}")
            await self._dispatch_event(event)

            self._current_event_idx += 1

            if self._current_event_idx >= len(self.events):
                logger.info("All Phase 1 scripted timeline events have completed.")
                await self.event_bus.publish(
                    "narrative.phase_1_completed",
                    transition_to=NarrativePhase.DIALOGUE,
                )
                break

    async def _dispatch_event(self, event: SceneEvent) -> None:
        """Dispatch scene effects and audio to the event bus."""
        for eff in event.effects:
            await self.event_bus.publish(
                "effect",
                payload={
                    "category": "visual" if "text" in eff.get("type", "") or "glitch" in eff.get("type", "") or "shake" in eff.get("type", "") else "system",
                    "name": eff.get("type"),
                    "params": eff.get("params", {}),
                    "priority": "normal",
                },
            )

        if event.audio:
            await self.event_bus.publish(
                "effect",
                payload={
                    "category": "audio",
                    "name": event.audio.get("type"),
                    "params": event.audio.get("params", {}),
                    "priority": "normal",
                },
            )
