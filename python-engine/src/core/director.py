"""Director — Central scene orchestrator for SENTIENT_OS v2."""

import asyncio
from typing import Any, Optional
from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.logger import get_logger
from src.infrastructure.platform.windows.file_scanner import WindowsFileScanner
from src.infrastructure.platform.windows.window_info import WindowsWindowInfo
from src.infrastructure.ws_server import WebSocketServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.scenes.crisis import FINALES_BY_PATH
from src.story.scenes.dialogue import (
    CHAT_CLOSE_REACTIONS,
    IDLE_BREAKERS,
    INITIAL_GREETINGS,
    WINDOW_FOCUS_LOST_REACTIONS,
)
from src.story.timeline import Timeline

logger = get_logger("director")


class Director:
    """Orchestrates AI brain, story engine, timeline, effect dispatching, and system triggers."""

    def __init__(
        self,
        event_bus: EventBus,
        brain: Brain,
        memory: Memory,
        personality: Personality,
        narrative: NarrativeStateMachine,
        timeline: Timeline,
        effect_decider: EffectDecider,
        ws_server: WebSocketServer,
        session_manager: SessionManager,
        config: Settings,
        file_scanner: Optional[WindowsFileScanner] = None,
        window_info: Optional[WindowsWindowInfo] = None,
    ):
        self.event_bus = event_bus
        self.brain = brain
        self.memory = memory
        self.personality = personality
        self.narrative = narrative
        self.timeline = timeline
        self.effect_decider = effect_decider
        self.ws_server = ws_server
        self.session_manager = session_manager
        self.config = config

        self.file_scanner = file_scanner or WindowsFileScanner()
        self.window_info = window_info or WindowsWindowInfo()

        self._message_count = 0
        self._is_active = False

    async def start(self) -> None:
        """Start Director event orchestration and subscribe to listeners."""
        self._is_active = True
        logger.info("Starting Director orchestration...")

        # Subscribe to IPC events
        await self.event_bus.subscribe("user_input", self.handle_user_input)
        await self.event_bus.subscribe("system_event", self.handle_system_event)
        await self.event_bus.subscribe("narrative.phase_1_completed", self._on_phase_1_completed)
        await self.event_bus.subscribe("onboarding_complete", self._on_onboarding_completed)

        # Start Phase 1 Timeline
        await self.timeline.start_phase(self.narrative.current_phase)

    async def handle_user_input(self, event_type: str, **kwargs: Any) -> None:
        """Process incoming user chat message."""
        text = kwargs.get("text", "")
        if not text:
            return

        self._message_count += 1
        logger.info(f"Director processing user message #{self._message_count}: '{text[:40]}'")

        # Gather system context
        system_info = {
            "streamer_mode": self.window_info.is_streamer_active(),
            "active_window": self.window_info.get_active_window_title(),
            "safe_files": self.file_scanner.scan_safe_files(),
        }

        # 1. Generate intelligent AI response
        ai_resp = await self.brain.generate_response(
            user_input=text,
            system_info=system_info,
            phase=int(self.narrative.current_phase),
            path=self.narrative.current_path,
        )

        # 2. Process and dispatch AI effects
        if ai_resp.actions:
            effect_cmds = self.effect_decider.process_actions(
                ai_resp.actions,
                phase=int(self.narrative.current_phase),
                emotion=ai_resp.emotion,
            )
            for cmd in effect_cmds:
                await self.event_bus.publish("effect", payload=cmd.to_ipc_payload())

        # 3. Broadcast ai_response message to Electron
        await self.event_bus.publish(
            "ai_response",
            payload={
                "speech": ai_resp.speech,
                "emotion": ai_resp.emotion,
                "internal_thought": ai_resp.internal_thought,
                "actions": ai_resp.actions,
                "narrative_signal": ai_resp.narrative_signal,
            },
        )

        # 4. Handle narrative signals and path progression
        if self.narrative.current_phase == NarrativePhase.DIALOGUE:
            path = self.personality.determine_path()
            self.narrative.set_candidate_path(path)

            if self.narrative.can_transition_to_crisis(signal=ai_resp.narrative_signal):
                await self.transition_to_phase(NarrativePhase.CRISIS)

    async def handle_system_event(self, event_type: str, **kwargs: Any) -> None:
        """Handle incoming Electron system events."""
        event_name = kwargs.get("event")
        data = kwargs.get("data", {})
        logger.debug(f"Director received system_event: {event_name}")

        if event_name == "idle_detected":
            idle_sec = float(data.get("idle_seconds", 45))
            self.timeline.set_idle_state(is_idle=True, idle_seconds=idle_sec)

            if self.narrative.current_phase == NarrativePhase.DIALOGUE:
                import random
                breaker_text = random.choice(IDLE_BREAKERS)
                await self.event_bus.publish(
                    "ai_response",
                    payload={"speech": breaker_text, "emotion": "sinister", "actions": []},
                )

        elif event_name == "chat_close_attempt":
            import random
            reaction = random.choice(CHAT_CLOSE_REACTIONS)
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": reaction, "emotion": "hurt", "actions": [{"type": "screen_shake", "params": {"intensity": 0.2, "duration_ms": 300}}]},
            )

        elif event_name == "window_focus_lost":
            import random
            reaction = random.choice(WINDOW_FOCUS_LOST_REACTIONS)
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": reaction, "emotion": "sinister", "actions": []},
            )

    async def _on_phase_1_completed(self, event_type: str, **kwargs: Any) -> None:
        """Called when Phase 1 timeline finishes."""
        logger.info("Phase 1 completed. Transitioning to Phase 2 Dialogue...")
        await self.transition_to_phase(NarrativePhase.DIALOGUE)

    async def _on_onboarding_completed(self, event_type: str, **kwargs: Any) -> None:
        """Called when Electron onboarding flow is finished."""
        logger.info("Onboarding completed by user. Starting narrative progression.")
        await self.timeline.start_phase(NarrativePhase.FIRST_CONTACT)

    async def transition_to_phase(self, new_phase: NarrativePhase) -> None:
        """Execute phase transition and trigger entrance events."""
        if not self.narrative.transition_to(new_phase):
            return

        # Save checkpoint
        await self.session_manager.save_checkpoint(
            label=f"phase_{new_phase.name.lower()}",
            narrative_state=self.narrative.state,
            personality_dict=self.personality.state.path_scores,
        )

        # Notify Electron of narrative phase change
        await self.event_bus.publish(
            "narrative_event",
            payload={
                "event": "phase_transition",
                "to_phase": int(new_phase),
                "path": self.narrative.current_path,
            },
        )

        if new_phase == NarrativePhase.DIALOGUE:
            # Open chat UI with initial greetings
            await self.event_bus.publish(
                "ui_command",
                payload={
                    "command": "open_chat",
                    "params": {"theme": "terminal", "initial_messages": INITIAL_GREETINGS},
                },
            )
            # Add initial greetings to AI working memory
            for g in INITIAL_GREETINGS:
                await self.memory.add_message(g["role"], g["content"], emotion="curious")

        elif new_phase == NarrativePhase.CRISIS:
            # Execute Climax Finale for locked path
            dominant_path = self.narrative.current_path or "curious"
            finale = FINALES_BY_PATH.get(dominant_path, FINALES_BY_PATH["curious"])
            logger.info(f"Initiating Climax Finale: '{finale.name}' (Theme: '{finale.theme}')")

            # Dispatch entrance effects
            for eff in finale.entrance_effects:
                await self.event_bus.publish("effect", payload=eff)

            # Change ambient mood
            await self.event_bus.publish(
                "ambient_change",
                payload={"mood": finale.ambient_mood, "fade_ms": 3000},
            )

            # Re-theme chat and deliver finale speech
            await self.event_bus.publish(
                "ui_command",
                payload={"command": "change_chat_theme", "params": {"theme": finale.theme}},
            )
            await self.event_bus.publish(
                "ai_response",
                payload={"speech": finale.initial_speech, "emotion": "sinister", "actions": []},
            )

    async def stop(self) -> None:
        """Stop director and active schedulers."""
        self._is_active = False
        await self.timeline.stop()
        logger.info("Director stopped cleanly.")
