"""SENTIENT_OS v2 Python Engine Entry Point."""

import asyncio
import ctypes
import os
import signal
import sys
from typing import Optional

# 1. Stdout Buffer configuration (Mandatory for IPC handshake communication)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

# 2. DPI Awareness configuration (Mandatory before Win32 calls and overlays)
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from src.config.settings import get_settings
from src.core.event_bus import EventBus
from src.core.safety import IsolatedKillSwitch, ResourceGuard, cleanup_tts_temp_files
from src.infrastructure.logger import get_logger, setup_logging, set_global_session_id
from src.infrastructure.persistence.database import init_database
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.privacy_filter import PrivacyFilter
from src.infrastructure.ws_server import WebSocketServer

logger = get_logger("main")


class EngineApp:
    """Main application orchestrator for Phase 1."""

    def __init__(self):
        self.settings = get_settings()
        setup_logging(log_dir=self.settings.log_dir)

        self.event_bus = EventBus()
        self.db_manager = None
        self.state_store = None
        self.ws_server = None
        self.kill_switch = None
        self.resource_guard = None
        self.privacy_filter = PrivacyFilter()
        self.shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Initialize all subsystems and run server."""
        logger.info("Initializing SENTIENT_OS v2 Python Engine...")

        # 1. Initial cleanup
        cleanup_tts_temp_files(self.settings.temp_dir)

        # 2. Initialize Persistence
        self.db_manager = await init_database(self.settings.db_path)
        self.state_store = StateStore(self.db_manager)

        # 3. Initialize WebSocket Server
        self.ws_server = WebSocketServer(
            event_bus=self.event_bus,
            host=self.settings.ws_host,
            port=self.settings.ws_port,
        )
        port = await self.ws_server.start()
        set_global_session_id(self.ws_server._session_id)

        # 4. Subscribe to events
        await self.event_bus.subscribe("safety.shutdown", self._on_safety_shutdown)
        await self.event_bus.subscribe("session.handshake_completed", self._on_handshake)
        await self.event_bus.subscribe("user_input", self._on_user_input)

        # 5. Start Safety systems
        if self.settings.kill_switch_enabled:
            self.kill_switch = IsolatedKillSwitch(
                restore_callback=self._restore_system_state,
                temp_dir=self.settings.temp_dir,
            )
            self.kill_switch.start()

        self.resource_guard = ResourceGuard(
            event_bus=self.event_bus,
            cpu_critical=self.settings.cpu_critical,
            ram_critical_mb=self.settings.ram_critical_mb,
        )
        self.resource_guard.start()

        logger.info(f"SENTIENT_OS v2 Engine is ready and running on port {port}")

    async def _on_handshake(self, event_type: str, **kwargs) -> None:
        session_id = kwargs.get("session_id", "sess_unknown")
        electron_pid = kwargs.get("electron_pid")
        logger.info(f"Handshake completed for session {session_id} (Electron PID: {electron_pid})")

        if self.kill_switch and electron_pid:
            self.kill_switch.set_electron_pid(electron_pid)

        # Create session in database
        if self.state_store:
            await self.state_store.create_session(
                session_id=session_id,
                language=self.settings.language,
                intensity=self.settings.intensity,
            )

    async def _on_user_input(self, event_type: str, **kwargs) -> None:
        """Echo/test handler for phase 1 validation."""
        text = kwargs.get("text", "")
        logger.info(f"User message received: {text}")

        # In Phase 1 foundation, respond with a confirmation message
        await self.event_bus.publish(
            "ai_response",
            payload={
                "speech": f"[SENTIENT Foundation Echo] Mesaj alındı: {text}",
                "emotion": "calm",
                "actions": [],
            },
        )

    async def _on_safety_shutdown(self, event_type: str, **kwargs) -> None:
        reason = kwargs.get("reason", "unknown")
        logger.critical(f"Safety shutdown triggered: {reason}")
        self.shutdown_event.set()

    def _restore_system_state(self) -> None:
        """Emergency restore callback for KillSwitch."""
        logger.info("Executing emergency system state restore...")

    async def stop(self) -> None:
        """Gracefully stop all services."""
        logger.info("Stopping SENTIENT_OS Engine...")

        if self.resource_guard:
            await self.resource_guard.stop()

        if self.ws_server:
            await self.ws_server.stop()

        if self.db_manager:
            await self.db_manager.close()

        cleanup_tts_temp_files(self.settings.temp_dir)
        logger.info("SENTIENT_OS Engine stopped cleanly.")

    async def run(self) -> None:
        await self.start()
        try:
            await self.shutdown_event.wait()
        finally:
            await self.stop()


def main() -> None:
    """CLI / Module entrypoint."""
    app = EngineApp()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _signal_handler():
        logger.info("Received termination signal")
        app.shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except (NotImplementedError, AttributeError):
            # Windows signal handler fallback
            pass

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
