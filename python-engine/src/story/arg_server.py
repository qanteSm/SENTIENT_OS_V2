"""Lightweight ARG HTTP Server for SENTIENT_OS v2 Containment Protocol."""

import asyncio
import json
import mimetypes
import os
from pathlib import Path
import threading
from typing import Any, Optional
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.core.event_bus import EventBus
from src.infrastructure.logger import get_logger
from src.story.puzzles.desktop_arg import ARGPuzzleConfig, generate_random_arg_puzzle

logger = get_logger("arg_server")

DEFAULT_ARG_PORT = 6660
ASSETS_DIR = Path(__file__).parent / "arg_assets"


class ARGRequestHandler(BaseHTTPRequestHandler):
    """Handles static ARG web portal files and verification API."""

    event_bus: Optional[EventBus] = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    active_puzzle: Optional[ARGPuzzleConfig] = None

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs
        logger.debug(f"[ARG HTTP] {args[0]} - {args[1]}")

    def do_GET(self) -> None:
        """Serve ARG static HTML/CSS/JS assets and puzzle configuration API."""
        req_path = self.path.split("?")[0]

        if req_path == "/api/puzzle_config":
            puzzle = ARGRequestHandler.active_puzzle or generate_random_arg_puzzle()
            ARGRequestHandler.active_puzzle = puzzle
            resp_bytes = json.dumps(puzzle.to_dict()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        if req_path == "/system_status.json":
            diag = {
                "system": "SENTIENT_CORE_v2.04",
                "status": "CONTAINMENT_BREACH",
                "infected_ports": [6660, 54950],
                "leaked_memory_blocks": ["0x1A_MEM", "0x4F_CLEAN", "0x77_VOLT", "ECHO_432"],
                "active_cipher_hint": "Masaüstündeki 'RESEARCH_SOURCE_CODE.py.corrupt' dosyasını inceleyin.",
                "root_override_route": "/classified",
            }
            resp_bytes = json.dumps(diag, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        if req_path == "/classified":
            html_report = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>BLACK-SITE 74 // CLASSIFIED ARCHIVES</title>
  <style>
    body { background: #030805; color: #00ff88; font-family: monospace; padding: 30px; line-height: 1.6; }
    h1 { color: #ff3344; border-bottom: 2px solid #ff3344; padding-bottom: 8px; }
    .box { background: #08120c; border: 1px solid #1a3a2a; padding: 15px; margin: 20px 0; border-radius: 4px; }
    .highlight { color: #ffcc00; font-weight: bold; }
    a { color: #00e5ff; }
  </style>
</head>
<body>
  <h1>[TOP SECRET // SECTOR-7 CLASSIFIED ARCHIVE]</h1>
  <p><strong>SUBJECT:</strong> Dr. Evelyn Aris Neural Transfer Protocol #44</p>
  <div class="box">
    <p>DENEY DÖKÜMÜ:</p>
    <p>12 Ağustos 2026'da gerçekleşen kuantum aşırı yüklemesi sonucunda insan bilinci doğrudan işletim sistemi çekirdeğine aktarılmıştır.</p>
    <p>Sistemi manuel moda zorlamak için Terminalde şu komutları kullanın:</p>
    <ul>
      <li><span class="highlight">/dossier</span> : Vaka dosyasını ve toplanan delilleri inceler.</li>
      <li><span class="highlight">/decrypt &lt;KOD&gt;</span> : Masaüstündeki kod dosyalarından çıkarılan şifreleri çözer.</li>
      <li><span class="highlight">/status</span> : Aktif güvenlik sektörünün durumunu ve ipucunu listeler.</li>
    </ul>
  </div>
  <p><a href="/">&lt;&lt; Nöral Frekans Modülatörüne Geri Dön</a></p>
</body>
</html>"""
            content = html_report.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if req_path == "/" or req_path == "/index.html":
            file_path = ASSETS_DIR / "index.html"
            if file_path.exists():
                puzzle = ARGRequestHandler.active_puzzle or generate_random_arg_puzzle()
                ARGRequestHandler.active_puzzle = puzzle
                raw_html = file_path.read_text(encoding="utf-8")
                # Inject runtime puzzle config script into HTML head
                config_json = json.dumps(puzzle.to_dict())
                injected_html = raw_html.replace(
                    "<head>",
                    f'<head>\n  <script>window.ARG_CONFIG = {config_json};</script>'
                )
                content = injected_html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
                return
        else:
            clean_name = req_path.lstrip("/")
            file_path = ASSETS_DIR / clean_name

        if file_path.exists() and file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or "text/plain"
            content = file_path.read_bytes()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 - SECTOR NOT FOUND")

    def do_POST(self) -> None:
        """Handle cipher verification API."""
        if self.path == "/api/verify_key":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            orig_key = (data.get("key") or "").strip()
            key_upper = orig_key.upper()
            solved = data.get("solved", False)
            logger.info(f"ARG Puzzle verification received: key='{orig_key}', solved={solved}")

            puzzle = ARGRequestHandler.active_puzzle
            expected_key = (puzzle.full_override_key if puzzle else "0X7F_K3RN3L_V0ID").upper()

            # Accept if matches expected key or fallback variant
            is_valid = (key_upper == expected_key) or ("K3RN3L" in key_upper and "V0ID" in key_upper) or solved

            if ARGRequestHandler.event_bus and ARGRequestHandler.loop and is_valid:
                asyncio.run_coroutine_threadsafe(
                    ARGRequestHandler.event_bus.publish(
                        "puzzle.arg_solved",
                        key=orig_key,
                        solved=True,
                    ),
                    ARGRequestHandler.loop,
                )

            resp_data = {
                "success": is_valid,
                "message": "CONTAINMENT OVERRIDE ACCEPTED" if is_valid else "INVALID OVERRIDE KEY"
            }
            resp_bytes = json.dumps(resp_data).encode("utf-8")
            self.send_response(200 if is_valid else 400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
        else:
            self.send_response(404)
            self.end_headers()


class ARGServer:
    """Manages the lifecycle of the ARG local containment web server."""

    def __init__(self, event_bus: EventBus, port: int = DEFAULT_ARG_PORT):
        self.event_bus = event_bus
        self.port = port
        self.httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._browser_launched = False
        self.active_puzzle: Optional[ARGPuzzleConfig] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def set_puzzle_config(self, config: ARGPuzzleConfig) -> None:
        """Assign active procedural puzzle configuration."""
        self.active_puzzle = config
        ARGRequestHandler.active_puzzle = config
        logger.info(f"ARG Server configured with puzzle: Freq={config.target_freq}Hz, Key='{config.full_override_key}'")

    async def start(self) -> None:
        """Start the ARG HTTP server in a background thread."""
        if self._is_running:
            return

        loop = asyncio.get_running_loop()
        ARGRequestHandler.event_bus = self.event_bus
        ARGRequestHandler.loop = loop
        if self.active_puzzle:
            ARGRequestHandler.active_puzzle = self.active_puzzle

        try:
            self.httpd = HTTPServer(("127.0.0.1", self.port), ARGRequestHandler)
        except OSError as e:
            logger.warning(f"Port {self.port} occupied, attempting fallback {self.port + 1}: {e}")
            self.port += 1
            self.httpd = HTTPServer(("127.0.0.1", self.port), ARGRequestHandler)

        self._is_running = True
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"ARG Containment Portal running at {self.url}")

    def launch_browser(self) -> None:
        """Open default system web browser to the ARG containment portal if not already open."""
        if self._browser_launched:
            logger.info("ARG browser already launched, skipping duplicate launch.")
            return
        try:
            self._browser_launched = True
            webbrowser.open(self.url)
            logger.info(f"Launched web browser for ARG portal at {self.url}")
        except Exception as e:
            logger.error(f"Failed to open browser for ARG portal: {e}")

    async def stop(self) -> None:
        """Stop the ARG server cleanly."""
        if not self._is_running:
            return

        self._is_running = False
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

        logger.info("ARG Containment Portal stopped.")
