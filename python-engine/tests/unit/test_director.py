"""Unit tests for Director scene orchestration and user message routing."""

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
async def test_director_orchestration(tmp_path):
    event_bus = EventBus()
    db_file = tmp_path / "director_test.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)
    session_id = "sess_director_test"

    session_mgr = SessionManager(state_store=state_store, session_id=session_id)
    await session_mgr.initialize()

    memory = Memory(session_id=session_id, state_store=state_store)
    personality = Personality()
    settings = Settings(gemini_api_key="")  # offline mode
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

    # Track AI responses
    ai_responses = []

    async def on_ai_response(event_type: str, **kwargs):
        ai_responses.append(kwargs.get("payload"))

    await event_bus.subscribe("ai_response", on_ai_response)

    # 1. Simulate transition to Phase 2 Dialogue
    await director.transition_to_phase(NarrativePhase.DIALOGUE)
    assert narrative.current_phase == NarrativePhase.DIALOGUE

    # 2. Simulate User Input message
    await director.handle_user_input("user_input", text="Burada mısın?")
    assert len(ai_responses) > 0
    assert "speech" in ai_responses[-1]

    # 3. Test /status command
    await director.handle_user_input("user_input", text="/status")
    assert "GÖREV & ÇEKİRDEK DURUMU" in ai_responses[-1]["speech"]

    # 4. Test /scan command
    await director.handle_user_input("user_input", text="/scan")
    assert "HIZLI TEHDİT TARAMASI" in ai_responses[-1]["speech"]

    # 5. Test /hack command
    await director.handle_user_input("user_input", text="/hack")
    assert "ANALİZ" in ai_responses[-1]["speech"] or "HEDEF" in ai_responses[-1]["speech"]

    # 6. Test /help command
    await director.handle_user_input("user_input", text="/help")
    assert "KOMUT REHBERİ" in ai_responses[-1]["speech"]

    # 7. Test /trial locked without decrypt
    await director.handle_user_input("user_input", text="/trial")
    assert "KİLİTLİ" in ai_responses[-1]["speech"]

    # 8. Test /decrypt command to unlock firewall
    await director.handle_user_input("user_input", text="/decrypt 0x1A_MEM")
    assert "DEŞİFRE EDİLDİ" in ai_responses[-1]["speech"]

    # 9. Test /trial command now unlocked and launching
    await director.handle_user_input("user_input", text="/trial")
    assert "SEKTÖR BAŞLATILIYOR" in ai_responses[-1]["speech"]

    # 10. Test /dossier command
    await director.handle_user_input("user_input", text="/dossier")
    assert "VAKA DOSYASI" in ai_responses[-1]["speech"]

    # 11. Test /logs command
    await director.handle_user_input("user_input", text="/logs")
    assert "GİZLİ KAYITLAR" in ai_responses[-1]["speech"]

    # Cleanup
    await director.stop()
    await ws_server.stop()
    await db_mgr.close()
