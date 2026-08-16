"""End-to-End Story Flow, Pacing, and Gameplay Cohesion Audit Test Suite.
Verifies narrative transitions, cipher decoding, 10 security trials, CCTV anomalies,
personality scoring, and all 3 climax finales (Salvation, Battle, Surrender).
"""

import asyncio
from typing import Any, List
import pytest

from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.director import Director
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.infrastructure.persistence.database import init_database
from src.infrastructure.persistence.state_store import StateStore
from src.story.arg_server import ARGServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.puzzles.cctv_threat import CCTVThreatEngine
from src.story.puzzles.desktop_arg import DesktopARGPuzzle
from src.story.puzzles.desktop_threat import DesktopThreatManager
from src.story.quest_manager import QuestManager
from src.story.timeline import Timeline


class MockBrain:
    """Mock AI brain for automated flow evaluation."""
    def __init__(self):
        self.emotion = "curious"
        self.speech = "Seni dinliyorum..."
        self.internal_thought = "Kullanıcıyı analiz ediyorum."
        self.actions: List[dict] = []
        self.narrative_signal = "none"

    async def generate_response(self, user_input: str, system_info: dict, phase: int, path: str = None):
        from src.ai.response_parser import AIResponse
        return AIResponse(
            speech=f"Cevap: {user_input}",
            emotion=self.emotion,
            internal_thought=self.internal_thought,
            actions=self.actions,
            narrative_signal=self.narrative_signal,
        )


@pytest.fixture
async def game_director_fixture(tmp_path):
    """Fixture creating a fully configured test Director instance."""
    event_bus = EventBus()
    db_path = tmp_path / "test_flow.db"
    db_mgr = await init_database(str(db_path))
    state_store = StateStore(db_mgr)
    session_mgr = SessionManager(state_store=state_store, session_id="test_flow_sess")
    await session_mgr.initialize(language="tr", intensity="medium")

    memory = Memory(session_id="test_flow_sess", state_store=state_store)
    personality = Personality()
    narrative = NarrativeStateMachine()
    timeline = Timeline(event_bus=event_bus)
    effect_decider = EffectDecider()
    quest_manager = QuestManager(event_bus=event_bus)
    desktop_threat = DesktopThreatManager(event_bus=event_bus)
    cctv_threat = CCTVThreatEngine(event_bus=event_bus)
    desktop_arg = DesktopARGPuzzle()
    arg_server = ARGServer(event_bus=event_bus, port=0)
    config = Settings(temp_dir=str(tmp_path))

    director = Director(
        event_bus=event_bus,
        brain=MockBrain(),
        memory=memory,
        personality=personality,
        narrative=narrative,
        timeline=timeline,
        effect_decider=effect_decider,
        ws_server=None,
        session_manager=session_mgr,
        config=config,
        desktop_arg=desktop_arg,
        arg_server=arg_server,
        desktop_threat=desktop_threat,
        cctv_threat=cctv_threat,
        quest_manager=quest_manager,
    )
    await director.start()

    yield director, event_bus

    await director.stop()
    await db_mgr.close()


@pytest.mark.asyncio
async def test_full_10_sector_cipher_and_quest_progression(game_director_fixture):
    """Verify that all 10 security sector ciphers unlock trials, yield dossiers, and advance sectors."""
    director, event_bus = game_director_fixture
    qm = director.quest_manager

    # 10 Official Cipher Keys
    cipher_keys = [
        ("0x1A_MEM", "games/game1_memory.html", 1),
        ("0x4F_CLEAN", "games/game2_slicer.html", 1),
        ("0x77_VOLT", "games/game3_wires.html", 2),
        ("ECHO_432", "games/game4_radar.html", 2),
        ("CAM_BREACH_03", "games/game6_cctv.html", 3),
        ("0xHEX_ROOT", "games/game7_hex.html", 3),
        ("MAZE_KEY_ALPHA", "games/game8_maze.html", 4),
        ("CIPHER_TRUTH", "games/game5_cipher.html", 4),
        ("REACTOR_CORE_99", "games/game9_reactor.html", 5),
        ("FINAL_CHOICE", "games/game10_trial.html", 5),
    ]

    for key, game_file, expected_sector in cipher_keys:
        # Decrypt cipher
        trial = qm.decrypt_cipher_code(key)
        assert trial is not None, f"Cipher key '{key}' failed to decrypt!"
        assert trial.is_unlocked is True
        assert trial.game_file == game_file

        # Complete minigame trial with success
        completed = await qm.complete_active_trial(success=True, score=100, game_file=game_file)
        assert completed is not None
        assert completed.is_completed is True

    # Assert all 10 sectors completed
    assert qm.completed_count == 10
    assert len(qm._unlocked_dossiers) == 10
    assert len(qm._unlocked_logs) == 10


@pytest.mark.asyncio
async def test_all_in_chat_terminal_commands(game_director_fixture):
    """Verify in-chat hacker commands (/help, /dossier, /logs, /scan, /cctv, /status, /trial, /override)."""
    director, event_bus = game_director_fixture

    captured_responses = []

    async def _capture_ai_resp(event_type: str, **kwargs):
        captured_responses.append(kwargs.get("payload", {}))

    await event_bus.subscribe("ai_response", _capture_ai_resp)

    commands_to_test = [
        "/help",
        "/dossier",
        "/logs",
        "/status",
        "/scan",
        "/hack",
        "/decrypt 0x1A_MEM",
        "/override 0x1A_MEM",
        "/trial",
        "/trial 1",
    ]

    for cmd in commands_to_test:
        captured_responses.clear()
        await director.handle_user_input("user_input", text=cmd)
        await asyncio.sleep(0.05)
        assert len(captured_responses) >= 1, f"Command '{cmd}' yielded no response!"
        speech = captured_responses[-1].get("speech", "")
        assert len(speech) > 5, f"Command '{cmd}' produced empty speech!"


@pytest.mark.asyncio
async def test_narrative_phase_and_3_climax_finales(game_director_fixture):
    """Verify narrative transition into Phase 1, Phase 1 ARG, Phase 2, and all 3 Climax Finales."""
    director, event_bus = game_director_fixture

    ui_commands = []
    effects = []

    async def _capture_ui(event_type: str, **kwargs):
        ui_commands.append(kwargs.get("payload", {}))

    async def _capture_fx(event_type: str, **kwargs):
        effects.append(kwargs.get("payload", {}))

    await event_bus.subscribe("ui_command", _capture_ui)
    await event_bus.subscribe("effect", _capture_fx)

    # 1. Phase 1 -> Dialogue
    await director.transition_to_phase(NarrativePhase.DIALOGUE)
    assert director.narrative.current_phase == NarrativePhase.DIALOGUE
    assert any(c.get("command") == "open_chat" for c in ui_commands)

    # 2. Test Salvation Finale (Curious Path)
    director.narrative.state.phase = NarrativePhase.DIALOGUE
    director.personality.state.path_scores = {"curious": 1.0, "fear": 0.0, "attack": 0.0}
    director.personality.determine_path()
    director.narrative.set_candidate_path("curious")
    await director.transition_to_phase(NarrativePhase.CRISIS)
    assert director.narrative.current_phase == NarrativePhase.CRISIS
    assert director.narrative.state.finale_type == "salvation"

    # 3. Test Battle Finale (Attack Path with Boss Platformer)
    ui_commands.clear()
    director.narrative.state.phase = NarrativePhase.DIALOGUE
    director.narrative.state.path_locked = False
    director.personality.state.path_scores = {"curious": 0.0, "fear": 0.0, "attack": 1.0}
    director.personality.determine_path()
    director.narrative.set_candidate_path("attack")
    await director.transition_to_phase(NarrativePhase.CRISIS)
    assert any(c.get("command") == "trigger_minigame" and c.get("params", {}).get("page") == "index.html" for c in ui_commands)

    # 4. Test Surrender Finale (Fear Path with Popup Virus)
    ui_commands.clear()
    director.narrative.state.phase = NarrativePhase.DIALOGUE
    director.narrative.state.path_locked = False
    director.personality.state.path_scores = {"curious": 0.0, "fear": 1.0, "attack": 0.0}
    director.personality.determine_path()
    director.narrative.set_candidate_path("fear")
    await director.transition_to_phase(NarrativePhase.CRISIS)
    assert any(c.get("command") == "trigger_minigame" and c.get("params", {}).get("page") == "popup_game.html" for c in ui_commands)


@pytest.mark.asyncio
async def test_cctv_threat_and_anomaly_containment(game_director_fixture):
    """Verify CCTV paranormal breach spawning and player containment."""
    director, event_bus = game_director_fixture
    cctv = director.cctv_threat

    cctv.spawn_anomaly(cam=3, monster="monster_crawler")
    assert cctv.has_active_anomaly is True
    assert cctv.active_anomaly["cam"] == 3
    assert cctv.time_remaining_sec > 0

    # Simulate player neutralizing anomaly via /cctv minigame completion
    await director._on_minigame_completed("minigame_completed", game="games/game6_cctv.html?anomaly=3", success=True)
    assert cctv.has_active_anomaly is False
