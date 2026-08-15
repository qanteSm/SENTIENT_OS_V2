"""Story Triggers system for responding to time, user idle, AI signals, and score thresholds."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TriggerContext:
    elapsed_seconds: float = 0.0
    idle_seconds: float = 0.0
    is_idle: bool = False
    current_phase: int = 1
    current_path: Optional[str] = None
    path_scores: dict[str, float] = field(default_factory=dict)
    signal: Optional[str] = None
    last_event: Optional[str] = None


@dataclass(frozen=True)
class TriggerAction:
    action_type: str  # "transition_phase" | "send_ai_prompt" | "play_scene" | "lock_path" | "notify"
    payload: dict[str, Any] = field(default_factory=dict)


class Trigger(ABC):
    """Abstract base trigger evaluated during game loop."""

    @abstractmethod
    def check(self, context: TriggerContext) -> bool:
        """Evaluate trigger condition."""
        pass

    @abstractmethod
    def get_action(self) -> TriggerAction:
        """Return associated action when triggered."""
        pass


class TimeTrigger(Trigger):
    """Triggers after a specific amount of time has elapsed in the phase."""

    def __init__(self, target_seconds: float, action: TriggerAction):
        self.target_seconds = target_seconds
        self.action = action
        self._fired = False

    def check(self, context: TriggerContext) -> bool:
        if not self._fired and context.elapsed_seconds >= self.target_seconds:
            self._fired = True
            return True
        return False

    def get_action(self) -> TriggerAction:
        return self.action

    def reset(self) -> None:
        self._fired = False


class IdleTrigger(Trigger):
    """Triggers when user has been inactive for a given duration."""

    def __init__(self, threshold_seconds: float, action: TriggerAction):
        self.threshold_seconds = threshold_seconds
        self.action = action
        self._fired = False

    def check(self, context: TriggerContext) -> bool:
        if context.is_idle and context.idle_seconds >= self.threshold_seconds:
            if not self._fired:
                self._fired = True
                return True
        else:
            self._fired = False  # Reset once active again
        return False

    def get_action(self) -> TriggerAction:
        return self.action


class SignalTrigger(Trigger):
    """Triggers when an AI narrative_signal matches."""

    def __init__(self, target_signal: str, action: TriggerAction):
        self.target_signal = target_signal
        self.action = action

    def check(self, context: TriggerContext) -> bool:
        return context.signal == self.target_signal

    def get_action(self) -> TriggerAction:
        return self.action


class EventTrigger(Trigger):
    """Triggers on specific system or UI event."""

    def __init__(self, target_event: str, action: TriggerAction):
        self.target_event = target_event
        self.action = action

    def check(self, context: TriggerContext) -> bool:
        return context.last_event == self.target_event

    def get_action(self) -> TriggerAction:
        return self.action


class ThresholdTrigger(Trigger):
    """Triggers when a score threshold is surpassed."""

    def __init__(self, score_key: str, threshold: float, action: TriggerAction):
        self.score_key = score_key
        self.threshold = threshold
        self.action = action
        self._fired = False

    def check(self, context: TriggerContext) -> bool:
        if not self._fired:
            val = context.path_scores.get(self.score_key, 0.0)
            if val >= self.threshold:
                self._fired = True
                return True
        return False

    def get_action(self) -> TriggerAction:
        return self.action
