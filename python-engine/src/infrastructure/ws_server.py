"""WebSocket Server implementation for Electron-Python IPC in SENTIENT_OS v2."""

import asyncio
import json
import sys
import time
import uuid
from typing import Any, Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol, serve

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger

logger = get_logger("ws_server")


class WebSocketServer:
    """Manages WebSocket communication with the Electron frontend."""

    def __init__(self, event_bus: EventBus, host: str = "127.0.0.1", port: int = 0):
        self.event_bus = event_bus
        self.host = host
        self.requested_port = port
        self.port: Optional[int] = None
        self._server = None
        self._clients: Set[WebSocketServerProtocol] = set()
        self._is_running = False
        self._session_id: str = f"sess_{uuid.uuid4().hex[:8]}"

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> int:
        """Start the WebSocket server, bind to port, and announce on stdout."""
        self._server = await serve(
            self._handle_client,
            self.host,
            self.requested_port,
            ping_interval=20,
            ping_timeout=30,
        )
        # Extract selected port (especially when port 0 is used)
        sockets = self._server.sockets
        if sockets and len(sockets) > 0:
            self.port = sockets[0].getsockname()[1]
        else:
            self.port = self.requested_port

        self._is_running = True
        logger.info(f"WebSocket server listening on ws://{self.host}:{self.port}")

        # Subscribe to outgoing events from EventBus
        await self._subscribe_to_outgoing_events()

        # Print WS_PORT for Electron process parent to read
        print(f"WS_PORT:{self.port}", flush=True)
        sys.stdout.flush()

        return self.port

    async def stop(self) -> None:
        """Gracefully stop server and close all client connections."""
        self._is_running = False
        # Send shutdown notification if clients are connected
        await self.broadcast("shutdown", {"reason": "server_stopping", "restore_required": True})

        for client in list(self._clients):
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connection lifecycle."""
        client_address = websocket.remote_address
        self._clients.add(websocket)
        logger.info(f"New client connected from {client_address}")

        try:
            async for raw_message in websocket:
                await self._process_raw_message(websocket, raw_message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client {client_address} disconnected (code={e.code}, reason={e.reason})")
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}", exc_info=True)
        finally:
            self._clients.discard(websocket)
            logger.info(f"Client {client_address} removed from active clients")

    async def _process_raw_message(
        self, websocket: WebSocketServerProtocol, raw_message: str | bytes
    ) -> None:
        """Parse JSON and route message to handlers or EventBus."""
        try:
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8")
            data = json.loads(raw_message)
        except Exception as e:
            logger.warning(f"Malformed JSON received: {e}")
            await self.send_to_client(
                websocket,
                "error",
                {
                    "error_code": "INVALID_MESSAGE",
                    "message": "Malformed JSON",
                },
            )
            return

        msg_type = data.get("type")
        msg_id = data.get("id", f"msg_{uuid.uuid4().hex[:6]}")
        payload = data.get("payload", {})

        if not msg_type:
            logger.warning("Message received without type")
            return

        logger.debug(f"Received message type='{msg_type}' id='{msg_id}'")

        # Handle handshake internally
        if msg_type == "handshake":
            electron_pid = payload.get("electron_pid")
            logger.info(f"Handshake received (Electron PID: {electron_pid})")
            ack_msg = {
                "type": "handshake_ack",
                "id": f"ack_{uuid.uuid4().hex[:6]}",
                "timestamp": int(time.time()),
                "payload": {
                    "status": "ready",
                    "session_id": self._session_id,
                    "resuming": False,
                },
            }
            await websocket.send(json.dumps(ack_msg))
            await self.event_bus.publish(
                "session.handshake_completed",
                session_id=self._session_id,
                electron_pid=electron_pid,
                payload=payload,
            )
            return

        # Handle kill_switch message from Electron
        if msg_type == "kill_switch":
            logger.warning("Kill switch triggered via WebSocket message")
            await self.event_bus.publish("safety.kill_switch_triggered", source="ws_ipc")
            return

        # Publish specific and general event to EventBus
        await self.event_bus.publish(
            f"ws.inbound.{msg_type}",
            msg_id=msg_id,
            timestamp=data.get("timestamp", int(time.time())),
            payload=payload,
            sender_ws=websocket,
        )
        await self.event_bus.publish(
            msg_type,
            msg_id=msg_id,
            timestamp=data.get("timestamp", int(time.time())),
            payload=payload,
            **payload,
        )

    async def send_to_client(
        self, websocket: WebSocketServerProtocol, msg_type: str, payload: dict[str, Any], msg_id: Optional[str] = None
    ) -> None:
        """Send a structured message to a specific client."""
        if msg_id is None:
            msg_id = f"out_{uuid.uuid4().hex[:6]}"

        message = {
            "type": msg_type,
            "id": msg_id,
            "timestamp": int(time.time()),
            "payload": payload,
        }
        try:
            await websocket.send(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send {msg_type} to client: {e}")

    async def broadcast(self, msg_type: str, payload: dict[str, Any], msg_id: Optional[str] = None) -> None:
        """Broadcast a message to all connected clients."""
        if not self._clients:
            logger.debug(f"No clients connected to receive broadcast '{msg_type}'")
            return

        if msg_id is None:
            msg_id = f"out_{uuid.uuid4().hex[:6]}"

        message = {
            "type": msg_type,
            "id": msg_id,
            "timestamp": int(time.time()),
            "payload": payload,
        }
        raw = json.dumps(message, ensure_ascii=False)
        tasks = [client.send(raw) for client in list(self._clients)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _subscribe_to_outgoing_events(self) -> None:
        """Subscribe to events that need to be forwarded to Electron."""
        outgoing_types = [
            "ai_response",
            "effect",
            "effect_chain",
            "tts_play",
            "ambient_change",
            "ui_command",
            "narrative_event",
            "shutdown",
        ]

        for evt in outgoing_types:
            await self.event_bus.subscribe(f"ws.outbound.{evt}", self._on_outgoing_event)
            await self.event_bus.subscribe(evt, self._on_direct_outgoing_event)

    async def _on_outgoing_event(self, event_type: str, **kwargs: Any) -> None:
        actual_type = event_type.replace("ws.outbound.", "")
        payload = kwargs.get("payload", kwargs)
        msg_id = kwargs.get("msg_id")
        await self.broadcast(actual_type, payload, msg_id)

    async def _on_direct_outgoing_event(self, event_type: str, **kwargs: Any) -> None:
        # Avoid double-broadcast if kwargs has already been broadcast
        if kwargs.get("_from_ws", False):
            return
        payload = kwargs.get("payload", kwargs)
        msg_id = kwargs.get("msg_id")
        await self.broadcast(event_type, payload, msg_id)
