"""Integration test for 3-Tier Memory pipeline."""

import pytest
from src.ai.context_builder import ContextBuilder
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore


@pytest.mark.asyncio
async def test_3_tier_memory_integration(tmp_path):
    db_file = tmp_path / "memory_integration.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    session_id = "sess_mem_integ"

    await state_store.create_session(session_id=session_id)

    async def mock_summarizer(messages):
        return f"Özet: {len(messages)} mesaj konuşuldu."

    memory = Memory(
        session_id=session_id,
        state_store=state_store,
        summary_generator=mock_summarizer,
        episodic_trigger_interval=5,
    )
    personality = Personality()
    builder = ContextBuilder()

    # Add 12 messages to trigger episodic summaries
    for i in range(12):
        await memory.add_message("user", f"Kullanıcı mesajı {i}")
        await memory.add_message("ai", f"Yapay zeka yanıtı {i}", emotion="calm")

    # Verify working memory FIFO max 20
    working = memory.get_working_memory()
    assert len(working) <= 20

    # Verify episodic summary was created and persisted
    episodes = await memory.get_recent_episodes()
    assert len(episodes) >= 1

    # Verify user profile entry
    await memory.update_profile_entry("fear_level", "high")
    profile = await memory.get_profile()
    assert profile.get("fear_level") == "high"

    # Verify prompt context builder includes profile and episodes
    context_str = builder.build_context_block(
        personality=personality,
        profile=profile,
        episodes=episodes,
        phase=2,
    )

    assert "fear_level=high" in context_str
    assert "Özet" in context_str

    await db_mgr.close()
