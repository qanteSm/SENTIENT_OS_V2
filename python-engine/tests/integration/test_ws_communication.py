"""Integration test for WebSocket handshake, message exchange, and session persistence."""

import asyncio
import json
import pytest
import websockets
from src.core.event_bus import EventBus
from src.infrastructure.persistence.database import DatabaseManager
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.ws_server import WebSocketServer


@pytest.mark.asyncio
async def test_websocket_handshake_and_echo_flow(tmp_path):
    event_bus = EventBus()
    db_file = tmp_path / "integration_test.db"
    db_mgr = DatabaseManager(str(db_file))
    await db_mgr.connect()
    state_store = StateStore(db_mgr)

    ws_server = WebSocketServer(event_bus=event_bus, host="127.0.0.1", port=0)
    port = await ws_server.start()

    # Subscribe echo handler
    async def echo_handler(event_type: str, **kwargs):
        text = kwargs.get("text", "")
        await event_bus.publish(
            "ai_response",
            payload={
                "speech": f"Echo: {text}",
                "emotion": "calm",
            },
        )

    await event_bus.subscribe("user_input", echo_handler)

    # Connect client
    uri = f"ws://127.0.0.1:{port}"
    async with websockets.connect(uri) as client:
        # 1. Send Handshake
        handshake_msg = {
            "type": "handshake",
            "id": "hs_001",
            "timestamp": 1234567,
            "payload": {
                "version": "2.0",
                "electron_pid": 9999,
                "platform": "win32",
            },
        }
        await client.send(json.dumps(handshake_msg))

        # 2. Receive Handshake Ack
        ack_raw = await asyncio.wait_for(client.recv(), timeout=5.0)
        ack_data = json.loads(ack_raw)

        assert ack_data["type"] == "handshake_ack"
        assert ack_data["payload"]["status"] == "ready"
        session_id = ack_data["payload"]["session_id"]
        assert session_id.startswith("sess_")

        # Create session in DB
        await state_store.create_session(session_id=session_id)

        # 3. Send User Input Message
        user_msg = {
            "type": "user_input",
            "id": "msg_001",
            "timestamp": 1234568,
            "payload": {
                "text": "Hello SENTIENT!",
            },
        }
        await client.send(json.dumps(user_msg))

        # 4. Receive AI Response Echo
        res_raw = await asyncio.wait_for(client.recv(), timeout=5.0)
        res_data = json.loads(res_raw)

        assert res_data["type"] == "ai_response"
        assert res_data["payload"]["speech"] == "Echo: Hello SENTIENT!"

    # Verify session persisted in SQLite
    session_row = await state_store.get_session(session_id)
    assert session_row is not None
    assert session_row["status"] == "active"

    # Cleanup
    await ws_server.stop()
    await db_mgr.close()
