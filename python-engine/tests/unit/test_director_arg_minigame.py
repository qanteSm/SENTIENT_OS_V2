"""Tests for Director ARG launch and Minigame Boss integration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.ai.brain import Brain
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import Settings
from src.core.director import Director
from src.core.event_bus import EventBus
from src.core.session import SessionManager
from src.story.arg_server import ARGServer
from src.story.effect_decider import EffectDecider
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.puzzles.desktop_arg import DesktopARGPuzzle
from src.story.timeline import Timeline


@pytest.fixture
def mock_director_env():
    event_bus = EventBus()
    config = Settings(intensity="medium")
    memory = Memory(session_id="test_sess")
    personality = Personality()
    narrative = NarrativeStateMachine()
    timeline = Timeline(event_bus=event_bus, events=[])
    effect_decider = EffectDecider()
    session_manager = MagicMock(spec=SessionManager)
    session_manager.save_checkpoint = AsyncMock()

    brain = MagicMock(spec=Brain)
    ws_server = MagicMock()

    arg_server = MagicMock(spec=ARGServer)
    arg_server.start = AsyncMock()
    arg_server.stop = AsyncMock()
    arg_server.launch_browser = MagicMock()
    arg_server.url = "http://127.0.0.1:6660"

    desktop_arg = MagicMock(spec=DesktopARGPuzzle)
    desktop_arg.deploy_puzzle_files = MagicMock(return_value=["SENTIENT_INCIDENT_REPORT_89.txt"])
    desktop_arg.cleanup = MagicMock()

    director = Director(
        event_bus=event_bus,
        brain=brain,
        memory=memory,
        personality=personality,
        narrative=narrative,
        timeline=timeline,
        effect_decider=effect_decider,
        ws_server=ws_server,
        session_manager=session_manager,
        config=config,
        arg_server=arg_server,
        desktop_arg=desktop_arg,
    )

    return director, event_bus, arg_server, desktop_arg, narrative


@pytest.mark.asyncio
async def test_phase_1_triggers_arg_boss_puzzle(mock_director_env):
    director, event_bus, arg_server, desktop_arg, narrative = mock_director_env
    await director.start()

    # Trigger phase 1 completion
    await event_bus.publish("narrative.phase_1_completed")
    await asyncio.sleep(0.05)

    desktop_arg.deploy_puzzle_files.assert_called_once()
    arg_server.start.assert_called_once()

    await director.stop()


@pytest.mark.asyncio
async def test_arg_puzzle_solved_transitions_to_dialogue(mock_director_env):
    director, event_bus, arg_server, desktop_arg, narrative = mock_director_env
    await director.start()

    # Trigger solve
    await event_bus.publish("puzzle.arg_solved", key="0x7F_K3RN3L_V0ID", solved=True)
    await asyncio.sleep(0.05)

    desktop_arg.cleanup.assert_called_once()
    arg_server.stop.assert_called_once()
    assert narrative.current_phase == NarrativePhase.DIALOGUE

    await director.stop()


@pytest.mark.asyncio
async def test_minigame_completed_delivers_response(mock_director_env):
    director, event_bus, arg_server, desktop_arg, narrative = mock_director_env
    await director.start()

    ai_response_received = asyncio.Event()
    received_payload = {}

    async def on_ai_response(event_type: str, **kwargs):
        nonlocal received_payload
        received_payload = kwargs.get("payload", {})
        ai_response_received.set()

    await event_bus.subscribe("ai_response", on_ai_response)

    # Trigger minigame victory
    await event_bus.publish("minigame_completed", success=True, score=1500)
    await asyncio.wait_for(ai_response_received.wait(), timeout=2.0)

    assert "MÜHÜRLENDİ" in received_payload.get("speech", "") or "başardın" in received_payload.get("speech", "")

    await director.stop()
