"""Unit tests for SQLite database initialization, WAL mode, and StateStore CRUD."""

import pytest
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore


@pytest.mark.asyncio
async def test_database_initialization_and_crud(tmp_path):
    db_file = tmp_path / "test_sentient.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()

    # Verify WAL mode PRAGMA
    async with db_mgr.connection.execute("PRAGMA journal_mode;") as cursor:
        row = await cursor.fetchone()
        assert row[0].lower() == "wal"

    store = StateStore(db_mgr)

    # 1. Session CRUD
    sess = await store.create_session("sess_test_123", language="tr", intensity="medium")
    assert sess["id"] == "sess_test_123"
    assert sess["status"] == "active"

    read_sess = await store.get_session("sess_test_123")
    assert read_sess is not None
    assert read_sess["id"] == "sess_test_123"

    await store.update_session("sess_test_123", status="completed", current_phase=2)
    updated = await store.get_session("sess_test_123")
    assert updated["status"] == "completed"
    assert updated["current_phase"] == 2

    # 2. Working Memory CRUD
    await store.add_working_memory("sess_test_123", "user", "Merhaba kimsin?")
    await store.add_working_memory("sess_test_123", "ai", "Ben SENTIENT.")
    memories = await store.get_working_memory("sess_test_123", limit=10)
    assert len(memories) == 2
    assert memories[0]["role"] == "user"
    assert memories[1]["role"] == "ai"

    # 3. Episodic Memory CRUD
    await store.add_episodic_memory("sess_test_123", "Kullanıcı ilk temas kurdu", importance=0.8)
    episodes = await store.get_episodic_memory("sess_test_123")
    assert len(episodes) == 1
    assert episodes[0]["summary"] == "Kullanıcı ilk temas kurdu"

    # 4. Checkpoints
    await store.save_checkpoint("sess_test_123", "phase_1_end", {"hp": 100, "phase": 1})
    latest_cp = await store.get_latest_checkpoint("sess_test_123")
    assert latest_cp is not None
    assert latest_cp["label"] == "phase_1_end"
    assert latest_cp["state"]["phase"] == 1

    # 5. User Profile
    await store.set_profile_value("temperament", "brave")
    await store.set_profile_value("stats", {"visits": 1})
    profile = await store.get_profile_dict()
    assert profile["temperament"] == "brave"
    assert profile["stats"] == {"visits": 1}

    # 6. Event Log
    log_id = await store.log_event("sess_test_123", "mouse_drift", {"dx": 10, "dy": 5})
    assert log_id > 0

    await db_mgr.close()
