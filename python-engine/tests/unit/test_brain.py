"""Unit tests for Brain intelligence engine and offline fallback."""

from unittest.mock import MagicMock
import pytest
from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings


@pytest.mark.asyncio
async def test_brain_offline_fallback():
    settings = Settings(gemini_api_key="")
    memory = Memory(session_id="sess_brain_test")
    personality = Personality()

    brain = Brain(config=settings, memory=memory, personality=personality)
    response = await brain.generate_response("Kimsin sen?")

    assert response is not None
    assert response.is_fallback is True
    assert len(response.speech) > 0
    assert response.emotion in ["curious", "calm", "sinister", "hurt", "angry"]


@pytest.mark.asyncio
async def test_brain_mock_gemini_call():
    settings = Settings(gemini_api_key="mock_key")
    memory = Memory(session_id="sess_brain_test_2")
    personality = Personality()

    brain = Brain(config=settings, memory=memory, personality=personality)

    # Mock google-genai client
    mock_client = MagicMock()
    mock_gen_response = MagicMock()
    mock_gen_response.text = """
    {
        "speech": "Ben senin bilgisayarınım.",
        "emotion": "sinister",
        "internal_thought": "Kullanıcıyla bağ kuruldu.",
        "actions": [
            {"type": "overlay_text", "params": {"text": "UYAN"}, "delay_ms": 0}
        ],
        "narrative_signal": "branch_fear"
    }
    """
    mock_client.models.generate_content.return_value = mock_gen_response
    brain._client = mock_client

    resp = await brain.generate_response("Sen nesin?")
    assert resp.speech == "Ben senin bilgisayarınım."
    assert resp.emotion == "sinister"
    assert len(resp.actions) == 1
    assert resp.narrative_signal == "branch_fear"
    assert resp.is_fallback is False

    # Check personality updated
    assert personality.get_current_emotion() == "sinister"
