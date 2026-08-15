"""SENTIENT_OS v2 Python Engine Entry Point."""

import argparse
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

from src.ai.brain import Brain
from src.ai.context_builder import ContextBuilder
from src.ai.memory import Memory
from src.ai.personality import Personality
from src.config.settings import get_settings
from src.core.event_bus import EventBus
from src.core.safety import IsolatedKillSwitch, ResourceGuard, cleanup_tts_temp_files
from src.infrastructure.logger import get_logger, setup_logging, set_global_session_id
from src.infrastructure.persistence.database import init_database
from src.infrastructure.persistence.state_store import StateStore
from src.infrastructure.platform.windows.file_scanner import WindowsFileScanner
from src.infrastructure.platform.windows.window_info import WindowsWindowInfo
from src.infrastructure.privacy_filter import PrivacyFilter
from src.infrastructure.ws_server import WebSocketServer

logger = get_logger("main")


class EngineApp:
    """Main application orchestrator for SENTIENT_OS v2."""

    def __init__(self, interactive_chat: bool = False):
        self.settings = get_settings()
        setup_logging(log_dir=self.settings.log_dir)
        self.interactive_chat = interactive_chat

        self.event_bus = EventBus()
        self.db_manager = None
        self.state_store = None
        self.ws_server = None
        self.kill_switch = None
        self.resource_guard = None

        self.privacy_filter = PrivacyFilter()
        self.file_scanner = WindowsFileScanner(self.privacy_filter)
        self.window_info = WindowsWindowInfo()

        self.personality = Personality()
        self.memory: Optional[Memory] = None
        self.brain: Optional[Brain] = None
        self.context_builder = ContextBuilder()

        self.shutdown_event = asyncio.Event()
        self.current_phase = 1
        self.current_path = None

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
        session_id = self.ws_server._session_id
        set_global_session_id(session_id)

        # 4. Initialize AI Domain & ensure session row exists in DB
        if self.state_store:
            await self.state_store.create_session(
                session_id=session_id,
                language=self.settings.language,
                intensity=self.settings.intensity,
                current_phase=self.current_phase,
            )

        self.memory = Memory(
            session_id=session_id,
            state_store=self.state_store,
            summary_generator=self._generate_summary_callback,
        )
        self.brain = Brain(
            config=self.settings,
            memory=self.memory,
            personality=self.personality,
            context_builder=self.context_builder,
        )

        # 5. Subscribe to events
        await self.event_bus.subscribe("safety.shutdown", self._on_safety_shutdown)
        await self.event_bus.subscribe("session.handshake_completed", self._on_handshake)
        await self.event_bus.subscribe("user_input", self._on_user_input)

        # 6. Start Safety systems
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

    async def _generate_summary_callback(self, messages):
        if self.brain:
            return await self.brain.generate_summary(messages)
        return ""

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
                current_phase=self.current_phase,
            )

    async def _on_user_input(self, event_type: str, **kwargs) -> None:
        """Process user chat input and generate AI response."""
        text = kwargs.get("text", "")
        if not text or not self.brain:
            return

        logger.info(f"User message received: {text}")

        # Gather system context
        system_info = {
            "streamer_mode": self.window_info.is_streamer_active(),
            "active_window": self.window_info.get_active_window_title(),
            "safe_files": self.file_scanner.scan_safe_files(),
        }

        # Generate intelligent response
        ai_resp = await self.brain.generate_response(
            user_input=text,
            system_info=system_info,
            phase=self.current_phase,
            path=self.current_path,
        )

        logger.info(f"AI [{ai_resp.emotion}]: {ai_resp.speech}")

        # Broadcast ai_response to Electron
        await self.event_bus.publish(
            "ai_response",
            payload={
                "speech": ai_resp.speech,
                "emotion": ai_resp.emotion,
                "internal_thought": ai_resp.internal_thought,
                "actions": ai_resp.actions,
                "narrative_signal": ai_resp.narrative_signal,
            },
        )

    async def _on_safety_shutdown(self, event_type: str, **kwargs) -> None:
        reason = kwargs.get("reason", "unknown")
        logger.critical(f"Safety shutdown triggered: {reason}")
        self.shutdown_event.set()

    def _restore_system_state(self) -> None:
        """Emergency restore callback for KillSwitch."""
        logger.info("Executing emergency system state restore...")

    async def run_terminal_chat(self) -> None:
        """Interactive terminal test loop for Faz 2."""
        print("\n" + "=" * 50)
        print("  SENTIENT_OS v2 — Terminal Chat Modu (Faz 2)")
        print("  Çıkmak için 'q' veya 'exit' yazın.")
        print("=" * 50 + "\n")

        system_info = {
            "streamer_mode": self.window_info.is_streamer_active(),
            "active_window": self.window_info.get_active_window_title(),
            "safe_files": self.file_scanner.scan_safe_files(),
        }

        while not self.shutdown_event.is_set():
            try:
                loop = asyncio.get_running_loop()
                user_msg = await loop.run_in_executor(None, lambda: input("\nSen: ").strip())
                if user_msg.lower() in ["q", "exit", "quit"]:
                    break

                if not user_msg:
                    continue

                response = await self.brain.generate_response(
                    user_input=user_msg,
                    system_info=system_info,
                    phase=self.current_phase,
                    path=self.current_path,
                )

                print(f"SENTIENT [{response.emotion}]: {response.speech}")
                if response.actions:
                    print(f"  [Actions: {response.actions}]")
                if response.narrative_signal != "none":
                    print(f"  [Signal: {response.narrative_signal}]")

            except (KeyboardInterrupt, EOFError):
                break

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
            if self.interactive_chat:
                await self.run_terminal_chat()
            else:
                await self.shutdown_event.wait()
        finally:
            await self.stop()


def main() -> None:
    """CLI / Module entrypoint."""
    parser = argparse.ArgumentParser(description="SENTIENT_OS v2 Python Engine")
    parser.add_argument(
        "--chat", action="store_true", help="Launch interactive terminal chat mode"
    )
    args = parser.parse_args()

    app = EngineApp(interactive_chat=args.chat)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def _signal_handler():
        logger.info("Received termination signal")
        app.shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except (NotImplementedError, AttributeError):
            pass

    try:
        loop.run_until_complete(app.run())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
