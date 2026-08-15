"""Unit tests for 3-layer Memory system."""

import pytest
from src.ai.memory import Memory
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore


@pytest.mark.asyncio
async def test_working_memory_fifo_limit():
    memory = Memory(session_id="test_sess", working_memory_limit=5)

    for i in range(10):
        await memory.add_message("user", f"Mesaj {i}")

    working = memory.get_working_memory()
    assert len(working) == 5
    assert working[0].content == "Mesaj 5"
    assert working[-1].content == "Mesaj 9"


@pytest.mark.asyncio
async def test_episodic_trigger(tmp_path):
    db_file = tmp_path / "mem_test.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    await state_store.create_session("sess_ep_test")

    summary_called = []

    async def mock_summary(messages):
        summary_called.append(len(messages))
        return "10 mesajlık temas özeti"

    memory = Memory(
        session_id="sess_ep_test",
        state_store=state_store,
        working_memory_limit=20,
        episodic_trigger_interval=3,  # Trigger every 3 messages for test
        summary_generator=mock_summary,
    )

    await memory.add_message("user", "1")
    await memory.add_message("ai", "2")
    assert len(summary_called) == 0

    await memory.add_message("user", "3")
    assert len(summary_called) == 1

    episodes = await memory.get_recent_episodes()
    assert len(episodes) == 1
    assert episodes[0].summary == "10 mesajlık temas özeti"

    await db_mgr.close()
