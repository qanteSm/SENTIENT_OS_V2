"""Unit tests for ContextBuilder prompt assembly."""

from src.ai.context_builder import ContextBuilder
from src.ai.personality import Personality
from src.ai.response_parser import Episode, Message


def test_build_system_prompt_phases():
    cb = ContextBuilder()

    p1 = cb.build_system_prompt(phase=1)
    assert "SENTIENT" in p1
    assert "İLK TEMAS" in p1

    p2 = cb.build_system_prompt(phase=2, path="curious")
    assert "DİYALOG" in p2
    assert "CURIOUS" in p2


def test_build_context_block():
    cb = ContextBuilder()
    personality = Personality()
    episodes = [Episode(id=1, summary="Kullanıcı ilk kez konuştu", importance=0.8, created_at="now")]
    profile = {"temperament": "brave"}
    system_info = {
        "safe_files": ["Proje.docx", "Resim.png"],
        "active_window": "Visual Studio Code",
        "streamer_mode": False,
    }

    block = cb.build_context_block(
        personality=personality,
        profile=profile,
        episodes=episodes,
        system_info=system_info,
        phase=2,
    )

    assert "Mevcut Faz: 2" in block
    assert "Proje.docx" in block
    assert "Visual Studio Code" in block
    assert "brave" in block
    assert "Kullanıcı ilk kez konuştu" in block


def test_format_conversation_history_limit():
    cb = ContextBuilder()
    messages = [
        Message(role="user", content=f"Mesaj {i}", timestamp="now")
        for i in range(50)
    ]

    history = cb.format_conversation_history(messages, max_chars=300)
    assert len(history) <= 400
    assert "Mesaj 49" in history
