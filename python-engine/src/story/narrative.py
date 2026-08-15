"""Narrative State Machine and Phase Progression for SENTIENT_OS v2."""

from dataclasses import dataclass, field
from enum import IntEnum
import time
from typing import Any, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("narrative")


class NarrativePhase(IntEnum):
    FIRST_CONTACT = 1   # 0-5 min: subtle anomalies, no direct chat
    DIALOGUE = 2        # 5-20 min: active conversational AI relationship
    CRISIS = 3          # 20-40 min: climax, path execution
    ENDED = 4           # Post-finale conclusion and cleanup


@dataclass
class NarrativeState:
    phase: NarrativePhase = NarrativePhase.FIRST_CONTACT
    phase_start_time: float = field(default_factory=time.time)
    path: Optional[str] = None          # "curious" | "fear" | "attack"
    path_locked: bool = False
    finale_type: Optional[str] = None   # "salvation" | "battle" | "surrender"
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": int(self.phase),
            "phase_start_time": self.phase_start_time,
            "path": self.path,
            "path_locked": self.path_locked,
            "finale_type": self.finale_type,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NarrativeState":
        return cls(
            phase=NarrativePhase(data.get("phase", 1)),
            phase_start_time=data.get("phase_start_time", time.time()),
            path=data.get("path"),
            path_locked=data.get("path_locked", False),
            finale_type=data.get("finale_type"),
            completed=data.get("completed", False),
        )


class NarrativeStateMachine:
    """Controls story phase transitions, path locking, and finale execution."""

    def __init__(self, initial_state: Optional[NarrativeState] = None):
        self.state = initial_state or NarrativeState()

    @property
    def current_phase(self) -> NarrativePhase:
        return self.state.phase

    @property
    def current_path(self) -> Optional[str]:
        return self.state.path

    def get_phase_elapsed_seconds(self) -> float:
        return max(0.0, time.time() - self.state.phase_start_time)

    def transition_to(self, new_phase: NarrativePhase) -> bool:
        """Transition narrative state machine to a new phase."""
        if new_phase <= self.state.phase and new_phase != NarrativePhase.FIRST_CONTACT:
            logger.warning(
                f"Ignoring backward/duplicate phase transition: {self.state.phase} -> {new_phase}"
            )
            return False

        old_phase = self.state.phase
        self.state.phase = new_phase
        self.state.phase_start_time = time.time()

        if new_phase == NarrativePhase.CRISIS and self.state.path:
            self.lock_path(self.state.path)

        logger.info(f"Narrative transition: Phase {old_phase.name} -> Phase {new_phase.name}")
        return True

    def set_candidate_path(self, path: str) -> None:
        """Update candidate path if not yet locked."""
        if self.state.path_locked:
            return
        if path in ["curious", "fear", "attack"]:
            self.state.path = path
            logger.debug(f"Candidate path updated to '{path}'")

    def lock_path(self, path: str) -> None:
        """Lock in final narrative path for Phase 3 Crisis."""
        self.state.path = path
        self.state.path_locked = True
        # Map path to finale type
        path_to_finale = {
            "curious": "salvation",
            "fear": "battle",
            "attack": "surrender",
        }
        self.state.finale_type = path_to_finale.get(path, "salvation")
        logger.info(f"Narrative path LOCKED: '{path}' (Finale: '{self.state.finale_type}')")

    def can_transition_to_dialogue(self, max_first_contact_sec: float = 300.0) -> bool:
        """Check if ready to transition from First Contact to Dialogue."""
        return (
            self.state.phase == NarrativePhase.FIRST_CONTACT
            and self.get_phase_elapsed_seconds() >= max_first_contact_sec
        )

    def can_transition_to_crisis(
        self, signal: Optional[str] = None, min_dialogue_sec: float = 600.0, max_dialogue_sec: float = 1200.0
    ) -> bool:
        """Check if ready to transition from Dialogue to Crisis."""
        if self.state.phase != NarrativePhase.DIALOGUE:
            return False

        elapsed = self.get_phase_elapsed_seconds()
        if elapsed >= max_dialogue_sec:
            return True
        if signal == "trigger_crisis" and elapsed >= min_dialogue_sec:
            return True
        return False
