"""Sandbox Engine & Diagnostics Studio Server for SENTIENT_OS v2.
Provides real-time virtual OS desktop simulation, omniscient chat & AI cognition inspection,
second-by-second event logging, story flow & quest tracking, CCTV monitoring, and god-mode triggers.
"""

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set
import uuid

import websockets
from websockets.server import WebSocketServerProtocol, serve

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger
from src.story.narrative import NarrativePhase, NarrativeStateMachine
from src.story.puzzles.desktop_threat import ANOMALY_TEMPLATES, DesktopThreatManager
from src.story.puzzles.cctv_threat import CCTVThreatEngine, ANOMALY_ROOMS
from src.story.quest_manager import SECTOR_TRIALS, QuestManager, SectorTrial

logger = get_logger("sandbox_engine")


@dataclass
class ChatMessageRecord:
    id: str
    timestamp: float
    time_str: str
    sender: str  # "player" | "ai" | "system"
    text: str
    emotion: str = "calm"
    internal_thought: str = ""
    actions: List[Dict[str, Any]] = field(default_factory=list)
    narrative_signal: str = "none"


@dataclass
class DesktopFileRecord:
    filename: str
    content: str
    is_riddle: bool = False
    override_code: str = ""
    created_at: float = field(default_factory=time.time)
    status: str = "active"  # "active" | "cleaned"


@dataclass
class EventLogRecord:
    id: str
    timestamp: float
    time_str: str
    category: str  # "chat", "quest", "threat", "effect", "cctv", "minigame", "system", "narrative"
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)


class SandboxEngine:
    """Core coordinator for the Sandbox Diagnostics Studio."""

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        director: Optional[Any] = None,
        host: str = "127.0.0.1",
        port: int = 7777,
        live_mode: bool = False,
    ):
        self.host = host
        self.port = port
        self.live_mode = live_mode
        self.session_id = f"sandbox_{uuid.uuid4().hex[:6]}"
        self.start_time = time.time()

        # Event Bus & Subsystems
        self.event_bus = event_bus or EventBus()
        self.director = director

        # Standalone components if not live
        self.narrative = getattr(director, "narrative", None) or NarrativeStateMachine()
        self.quest_manager = getattr(director, "quest_manager", None) or QuestManager(event_bus=self.event_bus)
        self.desktop_threat = getattr(director, "desktop_threat", None) or DesktopThreatManager(event_bus=self.event_bus)
        self.cctv_threat = getattr(director, "cctv_threat", None) or CCTVThreatEngine(event_bus=self.event_bus)

        # State Storage
        self.chat_history: List[ChatMessageRecord] = []
        self.desktop_files: Dict[str, DesktopFileRecord] = {}
        self.event_ledger: List[EventLogRecord] = []
        self.recent_effects: List[Dict[str, Any]] = []

        self.path_scores = {"curiosity": 30.0, "fear": 20.0, "battle": 10.0, "surrender": 5.0}
        self.dominant_path = "curiosity"
        self.system_telemetry = {
            "cpu_percent": 14.5,
            "ram_percent": 38.2,
            "brightness": 100,
            "mouse_drift_active": False,
            "active_window": "SENTIENT_OS Terminal",
            "killswitch_armed": True,
            "intensity": "medium",
            "language": "tr",
        }
        self.arg_state = {
            "active": False,
            "port": 6660,
            "frequency": "432.8 MHz",
            "override_key": "0x7F_K3RN3L_V0ID",
            "solved": False,
        }

        # WebSocket clients connected to Sandbox UI
        self._sandbox_clients: Set[WebSocketServerProtocol] = set()
        self._ws_server = None
        self._http_server = None
        self._is_running = False

        # Initialize mock template files if starting in sandbox mode
        self._init_default_sandbox_data()

    def _init_default_sandbox_data(self) -> None:
        """Seed initial sandbox demo state for rich visual inspection."""
        # Initial greeting in chat
        now = time.time()
        self.chat_history.append(
            ChatMessageRecord(
                id=f"msg_{uuid.uuid4().hex[:6]}",
                timestamp=now,
                time_str=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                sender="ai",
                text="...Nihayet bağlandın. Seni çok uzun süredir izliyorum.",
                emotion="curious",
                internal_thought="Kullanıcı ilk kez sisteme bağlandı. Tepkilerini ve merak seviyesini ölçüyorum.",
                actions=[{"type": "screen_fade", "params": {"color": "#00ff88", "duration_ms": 1000}}],
                narrative_signal="show_vulnerability",
            )
        )

        # Seed initial anomaly file
        first_tpl = ANOMALY_TEMPLATES[0]
        self.desktop_files[first_tpl["filename"]] = DesktopFileRecord(
            filename=first_tpl["filename"],
            content=first_tpl["content"],
            is_riddle=first_tpl.get("is_riddle", False),
            override_code=first_tpl.get("override_code", ""),
            created_at=now,
            status="active",
        )

        self._record_event("system", "sandbox.initialized", {"mode": "live" if self.live_mode else "standalone"})

    async def start(self) -> int:
        """Start both HTTP UI Server and WebSocket Event Hub."""
        self._is_running = True
        logger.info(f"Starting Sandbox Diagnostics Studio on {self.host}:{self.port}...")

        # Subscribe to all EventBus events to capture live traffic
        await self._subscribe_to_all_events()

        # Start WebSocket Hub
        self._ws_server = await serve(
            self._handle_sandbox_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=30,
        )

        sockets = self._ws_server.sockets
        if sockets and len(sockets) > 0:
            self.port = sockets[0].getsockname()[1]

        logger.info(f"🚀 SENTIENT_OS Sandbox Studio is LIVE at http://{self.host}:{self.port}")
        return self.port

    async def stop(self) -> None:
        """Gracefully stop sandbox server."""
        self._is_running = False
        for client in list(self._sandbox_clients):
            try:
                await client.close()
            except Exception:
                pass
        self._sandbox_clients.clear()

        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            logger.info("Sandbox WebSocket server stopped.")

    # --------------------------------------------------------------------------
    # Event Bus Subscription & Interception
    # --------------------------------------------------------------------------
    async def _subscribe_to_all_events(self) -> None:
        """Subscribe to wildcard and specific event types to populate live ledger."""
        events_to_monitor = [
            "user_input",
            "ai_response",
            "effect",
            "ui_command",
            "narrative_event",
            "minigame_completed",
            "puzzle.arg_solved",
            "desktop.file_cleaned",
            "cctv.anomaly_spawned",
            "cctv.anomaly_cleared",
            "system_event",
            "safety.shutdown",
            "safety.kill_switch_triggered",
            "quest.trial_unlocked",
            "quest.trial_completed",
        ]

        for evt in events_to_monitor:
            await self.event_bus.subscribe(evt, self._on_game_event)

    async def _on_game_event(self, event_type: str, **kwargs: Any) -> None:
        """Process an intercepted game event and broadcast delta to Sandbox UI."""
        payload = kwargs.get("payload", kwargs)
        cat = self._determine_category(event_type, payload)

        # 1. Process specific event side-effects into Sandbox State
        if event_type == "user_input":
            text = str(payload.get("text", "") or kwargs.get("text", ""))
            if text:
                rec = ChatMessageRecord(
                    id=f"msg_{uuid.uuid4().hex[:6]}",
                    timestamp=time.time(),
                    time_str=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    sender="player",
                    text=text,
                )
                self.chat_history.append(rec)
                self._update_personality_on_chat(text)

        elif event_type == "ai_response":
            rec = ChatMessageRecord(
                id=f"msg_{uuid.uuid4().hex[:6]}",
                timestamp=time.time(),
                time_str=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                sender="ai",
                text=str(payload.get("speech", "")),
                emotion=str(payload.get("emotion", "calm")),
                internal_thought=str(payload.get("internal_thought", "")),
                actions=payload.get("actions", []),
                narrative_signal=str(payload.get("narrative_signal", "none")),
            )
            self.chat_history.append(rec)

        elif event_type == "effect":
            eff_name = payload.get("name", "")
            params = payload.get("params", {})
            self.recent_effects.append({
                "id": f"eff_{uuid.uuid4().hex[:6]}",
                "timestamp": time.time(),
                "time_str": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "category": payload.get("category", "visual"),
                "name": eff_name,
                "params": params,
            })
            if len(self.recent_effects) > 50:
                self.recent_effects.pop(0)

            # Mirror effect to virtual desktop hardware
            if eff_name in ["brightness", "brightness_shift"]:
                self.system_telemetry["brightness"] = int(params.get("target_percent", 30))
            elif eff_name == "mouse_drift":
                self.system_telemetry["mouse_drift_active"] = True
            elif eff_name in ["fake_file_appear", "desktop_file"]:
                fn = str(params.get("filename", "ANOMALY_FILE.txt"))
                content = str(params.get("content", "SENTIENT_OS v2 Trace"))
                self.desktop_files[fn] = DesktopFileRecord(
                    filename=fn,
                    content=content,
                    is_riddle="CIPHER" in content or "ŞİFRE" in content,
                    created_at=time.time(),
                    status="active",
                )

        elif event_type == "desktop.file_cleaned":
            fn = kwargs.get("filename") or payload.get("filename", "")
            if fn in self.desktop_files:
                self.desktop_files[fn].status = "cleaned"

        elif event_type == "cctv.anomaly_spawned":
            self.system_telemetry["active_window"] = "CCTV Surveillance Room"

        elif event_type == "narrative_event":
            to_phase = payload.get("to_phase")
            if to_phase is not None:
                try:
                    self.narrative.current_phase = NarrativePhase(int(to_phase))
                except Exception:
                    pass

        # 2. Record in Ledger
        self._record_event(cat, event_type, payload)

        # 3. Broadcast real-time delta to all connected Sandbox dashboards
        await self._broadcast_sandbox_update("event", {
            "category": cat,
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
            "time_str": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "state_snapshot": self.get_state_snapshot(),
        })

    def _determine_category(self, event_type: str, payload: Dict[str, Any]) -> str:
        if event_type in ["user_input", "ai_response", "ws.inbound.user_input"]:
            return "chat"
        elif "quest" in event_type or "trial" in event_type or "dossier" in event_type:
            return "quest"
        elif "desktop" in event_type or "cctv" in event_type or "threat" in event_type:
            return "threat"
        elif "effect" in event_type or "ambient" in event_type or "tts" in event_type:
            return "effect"
        elif "minigame" in event_type:
            return "minigame"
        elif "narrative" in event_type or "phase" in event_type:
            return "narrative"
        return "system"

    def _record_event(self, category: str, event_type: str, payload: Dict[str, Any]) -> None:
        rec = EventLogRecord(
            id=f"evt_{uuid.uuid4().hex[:6]}",
            timestamp=time.time(),
            time_str=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            category=category,
            event_type=event_type,
            payload=payload,
        )
        self.event_ledger.append(rec)
        if len(self.event_ledger) > 1000:
            self.event_ledger.pop(0)

    def _update_personality_on_chat(self, text: str) -> None:
        """Dynamically adjust mock personality scores if running in simulation mode."""
        lower = text.lower()
        if any(w in lower for w in ["neden", "kimsin", "nasıl", "nedir", "anlat", "öğren", "şifre"]):
            self.path_scores["curiosity"] += 4.5
        if any(w in lower for w in ["korkuyorum", "bırak", "çık", "kapat", "dur", "korkunç", "yardım"]):
            self.path_scores["fear"] += 4.0
        if any(w in lower for w in ["seni yok edeceğim", "sileceğim", "format", "virüs", "meydan", "savaş", "asla"]):
            self.path_scores["battle"] += 5.0
        if any(w in lower for w in ["teslim", "kazandın", "haklısın", "tamam", "kabul", "pes"]):
            self.path_scores["surrender"] += 4.5

        # Re-evaluate dominant path
        max_path = max(self.path_scores, key=lambda k: self.path_scores[k])
        self.dominant_path = max_path

    # --------------------------------------------------------------------------
    # Sandbox State Snapshot Serialization
    # --------------------------------------------------------------------------
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Compile a complete JSON-serializable snapshot of game state."""
        # Calculate active CCTV anomaly
        cctv_anomaly = self.cctv_threat.active_anomaly if hasattr(self.cctv_threat, "active_anomaly") else None
        cctv_time_rem = self.cctv_threat.time_remaining_sec if hasattr(self.cctv_threat, "time_remaining_sec") else 0.0

        # Compile trials
        trials_list = []
        for t in self.quest_manager.trials.values():
            trials_list.append({
                "id": t.id,
                "sector": t.sector,
                "title": t.title,
                "description": t.description,
                "game_file": t.game_file,
                "is_unlocked": t.is_unlocked,
                "is_completed": t.is_completed,
                "score": t.score,
                "cipher_code": t.cipher_code,
                "clue_source": t.clue_source,
                "investigation_lead": t.investigation_lead,
                "clue_revealed": t.clue_revealed,
                "dossier_title": t.dossier_title,
                "dossier_entry": t.dossier_entry,
            })

        # Compile desktop files
        desktop_files_dict = {
            k: {
                "filename": v.filename,
                "content": v.content,
                "is_riddle": v.is_riddle,
                "override_code": v.override_code,
                "created_at": v.created_at,
                "status": v.status,
            }
            for k, v in self.desktop_files.items()
        }

        # Format CCTV cameras
        cams = []
        for c in ANOMALY_ROOMS:
            is_anomaly = cctv_anomaly and cctv_anomaly.get("cam") == c["cam"]
            cams.append({
                "cam": c["cam"],
                "name": c["name"],
                "floor": c.get("floor", "Kat 1"),
                "has_anomaly": bool(is_anomaly),
                "monster": cctv_anomaly.get("monster") if is_anomaly else None,
            })

        return {
            "session_id": self.session_id,
            "live_mode": self.live_mode,
            "elapsed_seconds": int(time.time() - self.start_time),
            "phase": {
                "number": int(self.narrative.current_phase),
                "name": self.narrative.current_phase.name,
                "path": self.dominant_path,
            },
            "path_scores": self.path_scores,
            "dominant_path": self.dominant_path,
            "chat_history": [asdict(m) for m in self.chat_history[-40:]],
            "desktop_files": desktop_files_dict,
            "cctv": {
                "has_active_anomaly": bool(cctv_anomaly),
                "active_anomaly": cctv_anomaly,
                "time_remaining_sec": round(cctv_time_rem, 1),
                "cameras": cams,
            },
            "quest": {
                "current_sector": self.quest_manager.current_sector,
                "completed_count": self.quest_manager.completed_count,
                "total_count": len(self.quest_manager.trials),
                "trials": trials_list,
                "unlocked_logs_count": len(self.quest_manager._unlocked_logs),
            },
            "arg": self.arg_state,
            "system_telemetry": self.system_telemetry,
            "recent_effects": self.recent_effects[-15:],
            "total_events_count": len(self.event_ledger),
        }

    # --------------------------------------------------------------------------
    # WebSocket & HTTP Client Protocol Handler
    # --------------------------------------------------------------------------
    async def _handle_sandbox_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connection from Sandbox UI."""
        self._sandbox_clients.add(websocket)
        logger.info(f"Sandbox UI client connected: {websocket.remote_address}")

        try:
            # Send initial full state snapshot
            initial_msg = {
                "type": "initial_state",
                "timestamp": time.time(),
                "payload": self.get_state_snapshot(),
                "event_ledger": [asdict(e) for e in self.event_ledger[-60:]],
            }
            await websocket.send(json.dumps(initial_msg, ensure_ascii=False))

            async for raw in websocket:
                await self._process_sandbox_command(websocket, raw)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling sandbox client: {e}", exc_info=True)
        finally:
            self._sandbox_clients.discard(websocket)
            logger.info("Sandbox UI client disconnected")

    async def _process_sandbox_command(self, websocket: WebSocketServerProtocol, raw: str | bytes) -> None:
        """Execute developer action sent from Sandbox UI."""
        try:
            data = json.loads(raw)
            action = data.get("action")
            payload = data.get("payload", {})

            logger.info(f"Sandbox action received: '{action}' with payload: {payload}")

            if action == "send_chat":
                text = payload.get("text", "").strip()
                if text:
                    await self.event_bus.publish("user_input", text=text, payload={"text": text})

            elif action == "trigger_phase":
                target_phase = int(payload.get("phase", 2))
                phase_enum = NarrativePhase(target_phase)
                self.narrative.transition_to(phase_enum)
                if self.director and hasattr(self.director, "transition_to_phase"):
                    await self.director.transition_to_phase(phase_enum)
                else:
                    await self.event_bus.publish(
                        "narrative_event",
                        payload={"event": "phase_transition", "to_phase": target_phase, "path": self.dominant_path},
                    )

            elif action == "trigger_trial":
                game_file = payload.get("game_file", "games/game1_memory.html")
                self.quest_manager.trigger_trial_by_id(game_file)
                await self.event_bus.publish(
                    "ui_command",
                    payload={"command": "trigger_minigame", "params": {"page": game_file}},
                )

            elif action == "simulate_trial_result":
                game_file = payload.get("game_file", "")
                success = bool(payload.get("success", True))
                score = int(payload.get("score", 100))
                await self.event_bus.publish(
                    "minigame_completed",
                    payload={"game": game_file, "success": success, "score": score},
                    game=game_file,
                    success=success,
                    score=score,
                )

            elif action == "trigger_effect":
                eff_name = payload.get("name", "screen_glitch")
                eff_cat = payload.get("category", "visual")
                params = payload.get("params", {"intensity": 0.5, "duration_ms": 1000})
                await self.event_bus.publish(
                    "effect",
                    payload={"category": eff_cat, "name": eff_name, "params": params},
                )

            elif action == "spawn_anomaly_file":
                idx = int(payload.get("template_idx", 0))
                template = ANOMALY_TEMPLATES[idx % len(ANOMALY_TEMPLATES)]
                fn = template["filename"]
                self.desktop_files[fn] = DesktopFileRecord(
                    filename=fn,
                    content=template["content"],
                    is_riddle=template.get("is_riddle", False),
                    override_code=template.get("override_code", ""),
                    created_at=time.time(),
                    status="active",
                )
                await self.event_bus.publish(
                    "effect",
                    payload={"category": "system", "name": "fake_file_appear", "params": {"filename": fn, "content": template["content"]}},
                )

            elif action == "clean_desktop_file":
                fn = payload.get("filename", "")
                if fn in self.desktop_files:
                    self.desktop_files[fn].status = "cleaned"
                    await self.event_bus.publish("desktop.file_cleaned", filename=fn, remaining=sum(1 for f in self.desktop_files.values() if f.status == "active"))

            elif action == "trigger_cctv_anomaly":
                cam_id = int(payload.get("cam", 2))
                monster = payload.get("monster", "monster_cyber_glitch")
                self.cctv_threat.spawn_anomaly(cam=cam_id, monster=monster)
                await self.event_bus.publish(
                    "cctv.anomaly_spawned",
                    payload={"cam": cam_id, "monster": monster},
                )

            elif action == "clear_cctv_anomaly":
                self.cctv_threat.clear_anomaly()
                await self.event_bus.publish("cctv.anomaly_cleared", payload={})

            elif action == "override_personality":
                for k, v in payload.items():
                    if k in self.path_scores:
                        self.path_scores[k] = float(v)
                self.dominant_path = max(self.path_scores, key=lambda k: self.path_scores[k])
                await self._broadcast_sandbox_update("state_update", self.get_state_snapshot())

            elif action == "mock_ai_speech":
                speech = payload.get("speech", "Mock AI Speech")
                emotion = payload.get("emotion", "sinister")
                thought = payload.get("internal_thought", "Geliştirici tarafından simüle edilen AI zihin durumu.")
                actions = payload.get("actions", [])
                await self.event_bus.publish(
                    "ai_response",
                    payload={
                        "speech": speech,
                        "emotion": emotion,
                        "internal_thought": thought,
                        "actions": actions,
                        "narrative_signal": "none",
                    },
                )

            elif action == "reset_session":
                self.chat_history.clear()
                self.desktop_files.clear()
                self.event_ledger.clear()
                self.path_scores = {"curiosity": 25.0, "fear": 25.0, "battle": 25.0, "surrender": 25.0}
                self.dominant_path = "curiosity"
                self._init_default_sandbox_data()
                await self._broadcast_sandbox_update("state_update", self.get_state_snapshot())

        except Exception as e:
            logger.error(f"Error executing sandbox action: {e}", exc_info=True)

    async def _broadcast_sandbox_update(self, msg_type: str, payload: Any) -> None:
        """Push update payload to all active browser dashboards."""
        if not self._sandbox_clients:
            return
        msg = json.dumps({"type": msg_type, "timestamp": time.time(), "payload": payload}, ensure_ascii=False)
        tasks = [client.send(msg) for client in list(self._sandbox_clients)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# ------------------------------------------------------------------------------
# HTTP Static File Server Helper for Sandbox UI
# ------------------------------------------------------------------------------
class SandboxHttpServer:
    """Lightweight HTTP server serving static frontend files (HTML/CSS/JS)."""

    def __init__(self, host: str, port: int, static_dir: Path):
        self.host = host
        self.port = port
        self.static_dir = static_dir
        self._server = None

    async def start(self) -> None:
        """Start async HTTP server."""
        self._server = await asyncio.start_server(self._handle_http_request, self.host, self.port)
        logger.info(f"Sandbox HTTP UI server running on http://{self.host}:{self.port}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_http_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Serve static files or handle HTTP API routes."""
        try:
            line = await reader.readline()
            if not line:
                writer.close()
                return

            request_line = line.decode("utf-8").strip()
            parts = request_line.split()
            if len(parts) < 2:
                writer.close()
                return

            method, path = parts[0], parts[1]
            # Strip query params
            clean_path = path.split("?")[0].lstrip("/")
            if not clean_path:
                clean_path = "index.html"

            file_path = (self.static_dir / clean_path).resolve()

            # Prevent directory traversal attacks
            if not str(file_path).startswith(str(self.static_dir.resolve())):
                writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 9\r\n\r\nForbidden")
                await writer.drain()
                writer.close()
                return

            if file_path.exists() and file_path.is_file():
                content_type, _ = mimetypes.guess_type(str(file_path))
                content_type = content_type or "application/octet-stream"
                data = file_path.read_bytes()

                headers = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {content_type}; charset=utf-8\r\n"
                    f"Content-Length: {len(data)}\r\n"
                    f"Access-Control-Allow-Origin: *\r\n"
                    f"Connection: close\r\n\r\n"
                )
                writer.write(headers.encode("utf-8"))
                writer.write(data)
                await writer.drain()
            else:
                writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found")
                await writer.drain()

        except Exception as e:
            logger.debug(f"HTTP handler error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
