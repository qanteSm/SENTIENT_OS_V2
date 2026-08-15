"""Integration test for end-to-end AI pipeline and effect dispatching."""

import pytest
from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.director import Director
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.ws_server import WebSocketServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.timeline import Timeline


@pytest.mark.asyncio
async def test_ai_pipeline_end_to_end(tmp_path):
    event_bus = EventBus()
    db_file = tmp_path / "pipeline_test.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    session_id = "sess_pipe_test"

    session_mgr = SessionManager(state_store=state_store, session_id=session_id)
    await session_mgr.initialize()

    memory = Memory(session_id=session_id, state_store=state_store)
    personality = Personality()
    settings = Settings(gemini_api_key="")  # Fallback template mode
    brain = Brain(config=settings, memory=memory, personality=personality)

    narrative = NarrativeStateMachine()
    timeline = Timeline(event_bus=event_bus, base_interval=0.01)
    effect_decider = EffectDecider()
    ws_server = WebSocketServer(event_bus=event_bus, host="127.0.0.1", port=0)
    await ws_server.start()

    director = Director(
        event_bus=event_bus,
        brain=brain,
        memory=memory,
        personality=personality,
        narrative=narrative,
        timeline=timeline,
        effect_decider=effect_decider,
        ws_server=ws_server,
        session_manager=session_mgr,
        config=settings,
    )
    await director.start()

    ai_responses = []

    async def on_ai_response(event_type: str, **kwargs):
        ai_responses.append(kwargs.get("payload"))

    await event_bus.subscribe("ai_response", on_ai_response)

    # 1. Advance to Phase 2 Dialogue
    await director.transition_to_phase(NarrativePhase.DIALOGUE)

    # 2. User sends message
    await director.handle_user_input("user_input", text="Korkmuyorum senden.")

    assert len(ai_responses) > 0
    resp = ai_responses[-1]
    assert "speech" in resp
    assert len(resp["speech"]) > 0
    assert resp["emotion"] in ["curious", "calm", "sinister", "hurt", "angry"]

    # 3. Check memory persisted in SQLite
    working_msgs = memory.get_working_memory()
    assert len(working_msgs) >= 2
    assert working_msgs[-2].content == "Korkmuyorum senden."

    await director.stop()
    await ws_server.stop()
    await db_mgr.close()
