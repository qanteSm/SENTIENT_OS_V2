"""Effect Decider for validating, bounding, and translating AI actions into IPC Effect commands."""

from dataclasses import dataclass, field
import uuid
from typing import Any, List, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("effect_decider")

# Allowed effect types per phase
PHASE_1_ALLOWED_EFFECTS = {
    "overlay_text",
    "mouse_drift",
    "screen_shake",
    "screen_glitch",
    "fake_file_appear",
    "fake_notification",
    "system_clock_shift",
    "log_message",
}

CRITICAL_PRIORITY_EFFECTS = {"fake_bsod", "kill_switch"}
HIGH_PRIORITY_EFFECTS = {"screen_glitch", "screen_shake", "tts_speak"}


@dataclass(frozen=True)
class EffectCommand:
    category: str  # "visual" | "audio" | "system" | "ui"
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # "critical" | "high" | "normal" | "low"
    delay_ms: int = 0
    id: str = field(default_factory=lambda: f"fx_{uuid.uuid4().hex[:6]}")

    def to_ipc_payload(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "name": self.name,
            "params": self.params,
            "priority": self.priority,
            "delay_ms": self.delay_ms,
        }


class EffectDecider:
    """Validates and bounds raw action payloads into structured EffectCommands."""

    def __init__(self):
        pass

    def _determine_category(self, action_name: str) -> str:
        if action_name in ["overlay_text", "screen_glitch", "screen_fade", "blackout", "flash", "screen_shake", "wallpaper_change"]:
            return "visual"
        if action_name in ["ambient_shift", "play_sfx", "play_stinger", "tts_speak"]:
            return "audio"
        if action_name in ["brightness", "brightness_shift", "mouse_drift", "mouse_freeze", "fake_notification", "fake_bsod", "fake_file_appear", "system_clock_shift", "log_message"]:
            return "system"
        return "ui"

    def _determine_priority(self, action_name: str) -> str:
        if action_name in CRITICAL_PRIORITY_EFFECTS:
            return "critical"
        if action_name in HIGH_PRIORITY_EFFECTS or action_name in ["blackout", "brightness"]:
            return "high"
        return "normal"

    def _bound_parameters(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Ensure numerical parameters stay within safe aesthetic bounds."""
        bounded = dict(params)

        if "intensity" in bounded:
            try:
                bounded["intensity"] = max(0.05, min(1.0, float(bounded["intensity"])))
            except (ValueError, TypeError):
                bounded["intensity"] = 0.5

        if "duration_ms" in bounded:
            try:
                bounded["duration_ms"] = max(100, min(15000, int(bounded["duration_ms"])))
            except (ValueError, TypeError):
                bounded["duration_ms"] = 2000

        if "target_percent" in bounded:
            try:
                bounded["target_percent"] = max(20, min(100, int(bounded["target_percent"])))
            except (ValueError, TypeError):
                bounded["target_percent"] = 30

        if "target_opacity" in bounded:
            try:
                bounded["target_opacity"] = max(0.0, min(1.0, float(bounded["target_opacity"])))
            except (ValueError, TypeError):
                bounded["target_opacity"] = 1.0

        if "volume" in bounded:
            try:
                bounded["volume"] = max(0.0, min(1.0, float(bounded["volume"])))
            except (ValueError, TypeError):
                bounded["volume"] = 0.5

        return bounded

    def process_actions(
        self, actions: List[dict[str, Any]], phase: int = 1, emotion: str = "calm"
    ) -> List[EffectCommand]:
        """Convert a list of raw action dictionaries into validated EffectCommands."""
        commands: List[EffectCommand] = []

        for act in actions:
            name = act.get("type", "")
            if not name:
                continue

            # In Phase 1, block aggressive effects
            if phase == 1 and name not in PHASE_1_ALLOWED_EFFECTS:
                logger.debug(f"Action '{name}' suppressed in Phase 1")
                continue

            category = self._determine_category(name)
            priority = self._determine_priority(name)
            raw_params = act.get("params", {})
            params = self._bound_parameters(name, raw_params)
            delay_ms = max(0, int(act.get("delay_ms", 0)))

            cmd = EffectCommand(
                category=category,
                name=name,
                params=params,
                priority=priority,
                delay_ms=delay_ms,
            )
            commands.append(cmd)

        return commands

    def create_effect_chain(
        self, commands: List[EffectCommand], chain_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Package multiple EffectCommands into a sequenced effect chain payload."""
        return {
            "chain_id": chain_id or f"chain_{uuid.uuid4().hex[:6]}",
            "effects": [
                {
                    "type": cmd.name,
                    "params": cmd.params,
                    "delay_ms": cmd.delay_ms,
                }
                for cmd in commands
            ],
        }
