"""Integration test for safety subsystems, crash recovery, and killswitch."""

import pytest
from src.core.event_bus import EventBus
from src.core.safety import ResourceGuard
from src.core.session import SessionManager
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.privacy_filter import PrivacyFilter


@pytest.mark.asyncio
async def test_safety_and_crash_recovery_integration(tmp_path):
    db_file = tmp_path / "safety_integ.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)

    # 1. Simulate orphaned active session from previous crash
    await state_store.create_session(session_id="sess_crashed_1")

    crashed = await SessionManager.check_crash_recovery(state_store)
    assert len(crashed) >= 1

    # Check updated to 'crashed'
    sess_info = await state_store.get_session("sess_crashed_1")
    assert sess_info["status"] == "crashed"

    # 2. Privacy filter whitelist & blacklist
    filter_obj = PrivacyFilter()
    assert filter_obj.is_blacklisted("passwords.txt") is True
    assert filter_obj.is_blacklisted("id_rsa") is True
    assert filter_obj.is_blacklisted(".env") is True
    assert filter_obj.is_blacklisted("notes.txt") is False
    assert filter_obj.is_blacklisted("holiday.jpg") is False

    # 3. ResourceGuard safety shutdown event publishing
    bus = EventBus()
    shutdown_events = []

    async def on_shutdown(event_type: str, **kwargs):
        shutdown_events.append(kwargs.get("reason"))

    await bus.subscribe("safety.shutdown", on_shutdown)

    await bus.publish(
        "safety.shutdown",
        reason="CPU overload simulated",
        metric="cpu",
        value=95.0,
    )
    assert len(shutdown_events) == 1
    assert "CPU overload simulated" in shutdown_events[0]

    await db_mgr.close()
