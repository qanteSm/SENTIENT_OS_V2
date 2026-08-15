"""AI Response models and JSON response parser for SENTIENT_OS v2."""

from dataclasses import dataclass, field
import json
import re
from typing import Any, List, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("response_parser")

VALID_EMOTIONS = {
    "curious",
    "amused",
    "hurt",
    "angry",
    "calm",
    "sinister",
    "sad",
    "excited",
}

VALID_ACTION_TYPES = {
    "overlay_text",
    "screen_glitch",
    "screen_fade",
    "screen_shake",
    "ambient_shift",
    "play_sfx",
    "play_stinger",
    "tts_speak",
    "mouse_drift",
    "mouse_freeze",
    "fake_notification",
    "fake_bsod",
    "fake_file_appear",
    "wallpaper_change",
    "brightness_shift",
    "chat_typing",
    "chat_style",
    "open_chat",
    "close_chat",
    "system_clock_shift",
    "log_message",
}

VALID_NARRATIVE_SIGNALS = {
    "none",
    "escalate",
    "de_escalate",
    "branch_curious",
    "branch_fear",
    "branch_attack",
    "trigger_crisis",
    "trigger_finale",
}


@dataclass(frozen=True)
class Message:
    role: str  # "user" | "ai" | "system"
    content: str
    timestamp: str
    emotion: str = "calm"


@dataclass(frozen=True)
class Episode:
    id: int
    summary: str
    importance: float
    created_at: str


@dataclass(frozen=True)
class AIResponse:
    speech: str
    emotion: str = "calm"
    internal_thought: str = ""
    actions: List[dict] = field(default_factory=list)
    memory_note: Optional[str] = None
    narrative_signal: str = "none"
    is_fallback: bool = False


class ParseError(Exception):
    """Raised when JSON cannot be parsed into a valid AIResponse."""
    pass


def extract_json_block(text: str) -> str:
    """Extract JSON object from markdown code blocks or raw text."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Match the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()

    return text


def parse_response(raw_text: str) -> AIResponse:
    """
    Parse and validate raw model output into an AIResponse instance.
    Handles JSON fences and field defaults.
    """
    json_str = extract_json_block(raw_text)
    try:
        data = json.loads(json_str)
    except Exception as e:
        logger.warning(f"Failed to parse AI response JSON: {e}. Raw content: {raw_text[:200]}")
        raise ParseError(f"Malformed JSON: {e}") from e

    if not isinstance(data, dict):
        raise ParseError("JSON payload is not a dictionary")

    speech = str(data.get("speech", "")).strip()
    if not speech:
        raise ParseError("Missing or empty 'speech' field in AI response")

    emotion = str(data.get("emotion", "calm")).lower().strip()
    if emotion not in VALID_EMOTIONS:
        logger.debug(f"Unknown emotion '{emotion}', defaulting to 'calm'")
        emotion = "calm"

    internal_thought = str(data.get("internal_thought", "")).strip()

    # Validate actions
    raw_actions = data.get("actions", [])
    valid_actions = []
    if isinstance(raw_actions, list):
        for act in raw_actions:
            if isinstance(act, dict) and "type" in act:
                act_type = str(act["type"]).strip()
                if act_type in VALID_ACTION_TYPES:
                    valid_actions.append(
                        {
                            "type": act_type,
                            "params": act.get("params", {}),
                            "delay_ms": int(act.get("delay_ms", 0)),
                        }
                    )

    memory_note = data.get("memory_note")
    if memory_note is not None:
        memory_note = str(memory_note).strip() or None

    narrative_signal = str(data.get("narrative_signal", "none")).lower().strip()
    if narrative_signal not in VALID_NARRATIVE_SIGNALS:
        narrative_signal = "none"

    return AIResponse(
        speech=speech,
        emotion=emotion,
        internal_thought=internal_thought,
        actions=valid_actions,
        memory_note=memory_note,
        narrative_signal=narrative_signal,
    )
