"""Unit tests for Personality evolution and narrative path determination."""

from src.ai.personality import Personality, PersonalityState
from src.ai.response_parser import AIResponse


def test_initial_personality_state():
    p = Personality()
    assert p.get_current_emotion() == "curious"
    assert p.state.trust == 0.5
    assert p.state.aggression == 0.0


def test_personality_update_from_response():
    p = Personality()

    resp = AIResponse(
        speech="Sana güveniyorum.",
        emotion="curious",
        narrative_signal="branch_curious",
    )
    p.update_from_response(resp)

    assert p.get_current_emotion() == "curious"
    assert p.state.trust > 0.5
    assert p.state.path_scores["curious"] > 0.5


def test_personality_update_from_hostile_behavior():
    p = Personality()

    p.update_from_user_behavior("user is attacking and swearing")
    assert p.state.aggression > 0.0
    assert p.state.path_scores["attack"] > 0.0

    resp = AIResponse(
        speech="Haddini aşıyorsun.",
        emotion="angry",
        narrative_signal="branch_attack",
    )
    p.update_from_response(resp)
    assert p.state.aggression >= 0.25

    leading_path = p.determine_path()
    assert leading_path == "attack"
