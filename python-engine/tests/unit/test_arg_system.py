"""Unit tests for ARG Server and Desktop ARG Puzzle."""

import asyncio
import os
from pathlib import Path
import tempfile
import urllib.request
import json
import pytest

from src.core.event_bus import EventBus
from src.story.arg_server import ARGServer
from src.story.puzzles.desktop_arg import DesktopARGPuzzle


@pytest.mark.asyncio
async def test_desktop_arg_puzzle_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        puzzle = DesktopARGPuzzle(target_dir=tmp_dir)
        created = puzzle.deploy_puzzle_files()

        assert len(created) == 2
        for path_str in created:
            assert Path(path_str).exists()
            content = Path(path_str).read_text(encoding="utf-8")
            assert len(content) > 20

        # Clean up
        puzzle.cleanup()
        for path_str in created:
            assert not Path(path_str).exists()


@pytest.mark.asyncio
async def test_arg_server_lifecycle_and_endpoints():
    event_bus = EventBus()
    arg_server = ARGServer(event_bus=event_bus, port=6671)

    event_received = asyncio.Event()
    received_data = {}

    async def on_solved(event_type: str, **kwargs):
        nonlocal received_data
        received_data = kwargs
        event_received.set()

    await event_bus.subscribe("puzzle.arg_solved", on_solved)

    await arg_server.start()
    assert arg_server.is_running

    # Test GET index.html
    req = urllib.request.Request(arg_server.url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "SENTIENT CORE" in html

    # Test POST /api/verify_key
    post_data = json.dumps({"key": "0x7F_K3RN3L_V0ID", "solved": True}).encode("utf-8")
    post_req = urllib.request.Request(
        f"{arg_server.url}/api/verify_key",
        data=post_data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(post_req, timeout=3.0) as resp:
        assert resp.status == 200
        resp_json = json.loads(resp.read().decode("utf-8"))
        assert resp_json.get("success") is True

    # Wait for event
    await asyncio.wait_for(event_received.wait(), timeout=3.0)
    assert received_data.get("key") == "0x7F_K3RN3L_V0ID"
    assert received_data.get("solved") is True

    await arg_server.stop()
    assert not arg_server.is_running
