"""SENTIENT_OS v2 — Sandbox Studio & Gameplay Diagnostics CLI Launcher.
Run with:
    python tools/sandbox.py
    python tools/sandbox.py --port 7777 --no-browser
"""

import argparse
import asyncio
import os
from pathlib import Path
import signal
import sys
import webbrowser

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.infrastructure.logger import get_logger, setup_logging
from src.tools.sandbox_engine import SandboxEngine, SandboxHttpServer

logger = get_logger("sandbox_cli")


async def run_sandbox(host: str, port: int, open_browser: bool, live_mode: bool) -> None:
    """Initialize and run the Sandbox server."""
    setup_logging()
    logger.info("Initializing SENTIENT_OS v2 Sandbox & Diagnostics Studio...")

    # Path to static UI folder
    static_ui_dir = BASE_DIR / "src" / "tools" / "sandbox_ui"

    # 1. Initialize Sandbox Engine (WebSocket & State Coordinator)
    engine = SandboxEngine(host=host, port=port, live_mode=live_mode)
    ws_port = await engine.start()

    # 2. Initialize Static HTTP Server (Serves the Web Studio UI)
    # If HTTP port is same as WS or dedicated, serve UI
    http_server = SandboxHttpServer(host=host, port=port + 1, static_dir=static_ui_dir)
    await http_server.start()

    studio_url = f"http://{host}:{port + 1}/index.html"
    print("\n" + "=" * 65)
    print("  🚀 SENTIENT_OS v2 — GAMEPLAY DIAGNOSTICS & SANDBOX STUDIO")
    print(f"  🌐 Web Studio Arayüzü: {studio_url}")
    print(f"  🔌 WebSocket IPC Hub: ws://{host}:{ws_port}")
    print("  ⚡ Mod: " + ("CANLI OYUN KÖPRÜSÜ" if live_mode else "STANDALONE LAB & SİMÜLATÖR"))
    print("  Çıkmak için CTRL+C tuşlarına basın.")
    print("=" * 65 + "\n")

    if open_browser:
        try:
            webbrowser.open(studio_url)
        except Exception:
            pass

    # Wait for shutdown signal or interrupt
    shutdown_event = asyncio.Event()

    try:
        while not shutdown_event.is_set():
            await asyncio.sleep(0.5)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        logger.info("Stopping Sandbox Studio...")
        try:
            await http_server.stop()
            await engine.stop()
        except Exception:
            pass
        logger.info("Sandbox Studio stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(description="SENTIENT_OS v2 Sandbox Studio")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7777, help="WebSocket Port (default: 7777, HTTP will be 7778)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    parser.add_argument("--live", action="store_true", help="Connect in live bridge mode to active engine")
    args = parser.parse_args()

    try:
        asyncio.run(
            run_sandbox(
                host=args.host,
                port=args.port,
                open_browser=not args.no_browser,
                live_mode=args.live,
            )
        )
    except KeyboardInterrupt:
        print("\n\n✅ SENTIENT_OS Sandbox Studio başarıyla kapatıldı.")


if __name__ == "__main__":
    main()
