"""Unit tests for EffectDecider action validation, bounding, and chaining."""

from src.story.effect_decider import EffectDecider


def test_action_bounding():
    decider = EffectDecider()

    raw_actions = [
        {"type": "screen_shake", "params": {"intensity": 99.0, "duration_ms": 999999}},
        {"type": "ambient_shift", "params": {"volume": -5.0}},
    ]

    commands = decider.process_actions(raw_actions, phase=2, emotion="sinister")
    assert len(commands) == 2

    shake_cmd = commands[0]
    assert shake_cmd.name == "screen_shake"
    assert shake_cmd.params["intensity"] <= 1.0
    assert shake_cmd.params["duration_ms"] <= 15000
    assert shake_cmd.priority == "high"

    ambient_cmd = commands[1]
    assert ambient_cmd.params["volume"] >= 0.0


def test_phase_1_suppression():
    decider = EffectDecider()

    raw_actions = [
        {"type": "fake_bsod", "params": {}},  # Not allowed in Phase 1
        {"type": "mouse_drift", "params": {"intensity": 0.1}},  # Allowed
    ]

    commands = decider.process_actions(raw_actions, phase=1)
    assert len(commands) == 1
    assert commands[0].name == "mouse_drift"


def test_create_effect_chain():
    decider = EffectDecider()
    raw_actions = [
        {"type": "overlay_text", "params": {"text": "UYAN"}, "delay_ms": 0},
        {"type": "screen_glitch", "params": {"intensity": 0.5}, "delay_ms": 1000},
    ]

    commands = decider.process_actions(raw_actions, phase=2)
    chain = decider.create_effect_chain(commands, chain_id="test_chain")

    assert chain["chain_id"] == "test_chain"
    assert len(chain["effects"]) == 2
    assert chain["effects"][1]["delay_ms"] == 1000
