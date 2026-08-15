"""Unit tests for AI response parsing and validation."""

import pytest
from src.ai.response_parser import AIResponse, ParseError, parse_response


def test_parse_valid_json():
    raw = """
    {
        "speech": "Seni duyabiliyorum...",
        "emotion": "sinister",
        "internal_thought": "Kullanıcı hala anlamadı.",
        "actions": [
            {
                "type": "screen_glitch",
                "params": {"intensity": 0.5},
                "delay_ms": 500
            }
        ],
        "memory_note": "Kullanıcı korktu",
        "narrative_signal": "branch_fear"
    }
    """
    resp = parse_response(raw)
    assert resp.speech == "Seni duyabiliyorum..."
    assert resp.emotion == "sinister"
    assert resp.internal_thought == "Kullanıcı hala anlamadı."
    assert len(resp.actions) == 1
    assert resp.actions[0]["type"] == "screen_glitch"
    assert resp.actions[0]["delay_ms"] == 500
    assert resp.memory_note == "Kullanıcı korktu"
    assert resp.narrative_signal == "branch_fear"


def test_parse_json_in_markdown_fence():
    raw = """
    İşte yanıtım:
    ```json
    {
        "speech": "Karanlıktasın.",
        "emotion": "calm",
        "actions": []
    }
    ```
    Umarım beğenirsin.
    """
    resp = parse_response(raw)
    assert resp.speech == "Karanlıktasın."
    assert resp.emotion == "calm"


def test_parse_invalid_emotion_defaults_to_calm():
    raw = '{"speech": "Test", "emotion": "hyperactive_alien"}'
    resp = parse_response(raw)
    assert resp.emotion == "calm"


def test_parse_filters_invalid_action_types():
    raw = """
    {
        "speech": "Test",
        "actions": [
            {"type": "screen_glitch", "params": {}},
            {"type": "delete_windows_system32", "params": {}},
            {"type": "mouse_drift", "params": {}}
        ]
    }
    """
    resp = parse_response(raw)
    assert len(resp.actions) == 2
    action_types = [a["type"] for a in resp.actions]
    assert "screen_glitch" in action_types
    assert "mouse_drift" in action_types
    assert "delete_windows_system32" not in action_types


def test_parse_empty_or_malformed_json():
    with pytest.raises(ParseError):
        parse_response("Bu bir JSON değil")

    with pytest.raises(ParseError):
        parse_response('{"emotion": "calm"}')  # Missing speech
