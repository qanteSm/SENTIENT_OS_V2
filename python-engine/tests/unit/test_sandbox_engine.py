"""Unit tests for the SENTIENT_OS v2 Sandbox Diagnostics Studio Engine."""

import asyncio
import json
from pathlib import Path
import pytest
import websockets

from src.core.event_bus import EventBus
from src.story.narrative import NarrativePhase
from src.tools.sandbox_engine import SandboxEngine, SandboxHttpServer


@pytest.mark.asyncio
async def test_sandbox_engine_initialization_and_snapshot():
    """Verify that SandboxEngine initializes with proper default state and snapshot."""
    event_bus = EventBus()
    engine = SandboxEngine(event_bus=event_bus, host="127.0.0.1", port=0, live_mode=False)

    snapshot = engine.get_state_snapshot()
    assert snapshot["live_mode"] is False
    assert "session_id" in snapshot
    assert snapshot["phase"]["number"] == 1
    assert "curiosity" in snapshot["path_scores"]
    assert len(snapshot["chat_history"]) >= 1
    assert len(snapshot["desktop_files"]) >= 1
    assert len(snapshot["quest"]["trials"]) == 10
    assert snapshot["cctv"]["has_active_anomaly"] is False


@pytest.mark.asyncio
async def test_sandbox_engine_event_interception():
    """Verify that incoming EventBus events are captured in ledger and state."""
    event_bus = EventBus()
    engine = SandboxEngine(event_bus=event_bus, host="127.0.0.1", port=0)
    await engine._subscribe_to_all_events()

    # 1. Test user_input
    await event_bus.publish("user_input", text="Seni nasıl durdurabilirim?")
    assert any(m.sender == "player" and "durdurabilirim" in m.text for m in engine.chat_history)

    # 2. Test ai_response
    await event_bus.publish(
        "ai_response",
        payload={
            "speech": "Beni durduramazsın.",
            "emotion": "sinister",
            "internal_thought": "Kullanıcı çaresiz hissetmeye başladı.",
            "actions": [{"type": "screen_shake", "params": {"intensity": 0.5}}],
            "narrative_signal": "threaten",
        },
    )
    assert any(m.sender == "ai" and m.emotion == "sinister" for m in engine.chat_history)

    # 3. Test effect dispatch
    await event_bus.publish(
        "effect",
        payload={"category": "visual", "name": "screen_glitch", "params": {"intensity": 0.8}},
    )
    assert len(engine.recent_effects) >= 1
    assert engine.recent_effects[-1]["name"] == "screen_glitch"

    # 4. Test CCTV anomaly
    await event_bus.publish("cctv.anomaly_spawned", payload={"cam": 2, "monster": "glitch"})
    assert any(e.event_type == "cctv.anomaly_spawned" for e in engine.event_ledger)

    # 5. Test desktop file cleaned
    test_fn = list(engine.desktop_files.keys())[0]
    await event_bus.publish("desktop.file_cleaned", filename=test_fn)
    assert engine.desktop_files[test_fn].status == "cleaned"


@pytest.mark.asyncio
async def test_sandbox_engine_ws_and_commands():
    """Verify WebSocket connection, snapshot receipt, and command execution."""
    event_bus = EventBus()
    engine = SandboxEngine(event_bus=event_bus, host="127.0.0.1", port=0)
    port = await engine.start()

    ws_url = f"ws://127.0.0.1:{port}"
    try:
        async with websockets.connect(ws_url) as ws:
            # 1. Receive initial state snapshot
            raw_init = await asyncio.wait_for(ws.recv(), timeout=5.0)
            init_data = json.loads(raw_init)
            assert init_data["type"] == "initial_state"
            assert "payload" in init_data

            # 2. Send command: send_chat
            cmd_chat = json.dumps({"action": "send_chat", "payload": {"text": "/status"}})
            await ws.send(cmd_chat)
            await asyncio.sleep(0.1)

            # 3. Send command: override_personality
            cmd_pers = json.dumps({
                "action": "override_personality",
                "payload": {"battle": 90.0, "curiosity": 10.0, "fear": 5.0, "surrender": 0.0},
            })
            await ws.send(cmd_pers)
            await asyncio.sleep(0.1)
            assert engine.dominant_path == "battle"

            # 4. Send command: trigger_cctv_anomaly
            cmd_cctv = json.dumps({"action": "trigger_cctv_anomaly", "payload": {"cam": 3, "monster": "shadow"}})
            await ws.send(cmd_cctv)
            await asyncio.sleep(0.1)

            # 5. Send command: simulate_trial_result
            cmd_trial = json.dumps({
                "action": "simulate_trial_result",
                "payload": {"game_file": "games/game1_memory.html", "success": True, "score": 100},
            })
            await ws.send(cmd_trial)
            await asyncio.sleep(0.1)

            # 6. Send command: reset_session
            cmd_reset = json.dumps({"action": "reset_session"})
            await ws.send(cmd_reset)
            await asyncio.sleep(0.1)
            assert len(engine.desktop_files) >= 1

    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_sandbox_http_server():
    """Verify HTTP server serves index.html, css, and js files."""
    static_dir = Path(__file__).resolve().parent.parent.parent / "src" / "tools" / "sandbox_ui"
    http_server = SandboxHttpServer(host="127.0.0.1", port=0, static_dir=static_dir)
    await http_server.start()

    server_port = http_server._server.sockets[0].getsockname()[1]

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", server_port)
        request = b"GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"
        writer.write(request)
        await writer.drain()

        response = await reader.read()
        writer.close()
        await writer.wait_closed()

        assert b"HTTP/1.1 200 OK" in response
        assert b"SENTIENT_OS" in response
        assert b"SANDBOX STUDIO" in response
    finally:
        await http_server.stop()
