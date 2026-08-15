"""Integration test for Phase 1 -> 2 -> 3 Story Flow and State Checkpoints."""

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
async def test_full_narrative_story_flow(tmp_path):
    event_bus = EventBus()
    db_file = tmp_path / "story_flow_test.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    session_id = "sess_story_test"

    session_mgr = SessionManager(state_store=state_store, session_id=session_id)
    await session_mgr.initialize()

    memory = Memory(session_id=session_id, state_store=state_store)
    personality = Personality()
    settings = Settings(gemini_api_key="")
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

    # Step 1: Start at First Contact
    assert narrative.current_phase == NarrativePhase.FIRST_CONTACT

    # Step 2: Transition to Dialogue
    await director.transition_to_phase(NarrativePhase.DIALOGUE)
    assert narrative.current_phase == NarrativePhase.DIALOGUE

    # Step 3: Checkpoint saved in SQLite
    latest_cp = await session_mgr.load_latest_checkpoint()
    assert latest_cp is not None
    assert latest_cp["label"] == "phase_dialogue"

    # Step 4: Simulate hostility -> personality determines attack path
    personality.update_from_user_behavior("hostile")
    dominant_path = personality.determine_path()
    assert dominant_path == "attack"
    narrative.set_candidate_path(dominant_path)

    # Step 5: Transition to Crisis Finale
    await director.transition_to_phase(NarrativePhase.CRISIS)
    assert narrative.current_phase == NarrativePhase.CRISIS
    assert narrative.state.path_locked is True
    assert narrative.state.finale_type == "surrender"

    await director.stop()
    await ws_server.stop()
    await db_mgr.close()
