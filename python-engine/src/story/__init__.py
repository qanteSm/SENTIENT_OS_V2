"""Story Domain package for SENTIENT_OS v2."""

from .effect_decider import EffectCommand, EffectDecider
from .narrative import NarrativePhase, NarrativeState, NarrativeStateMachine
from .timeline import Timeline
from .triggers import (
    EventTrigger,
    IdleTrigger,
    SignalTrigger,
    ThresholdTrigger,
    TimeTrigger,
    Trigger,
    TriggerAction,
    TriggerContext,
)

__all__ = [
    "NarrativePhase",
    "NarrativeState",
    "NarrativeStateMachine",
    "Timeline",
    "EffectDecider",
    "EffectCommand",
    "Trigger",
    "TriggerAction",
    "TriggerContext",
    "TimeTrigger",
    "IdleTrigger",
    "SignalTrigger",
    "EventTrigger",
    "ThresholdTrigger",
]
