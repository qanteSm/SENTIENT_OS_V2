"""Unit tests for ResourceGuard safety limits and cleanup functions."""

import asyncio
from unittest.mock import MagicMock, patch
import pytest

from src.core.event_bus import EventBus
from src.core.safety import ResourceGuard, cleanup_tts_temp_files


@pytest.mark.asyncio
async def test_resource_guard_thresholds():
    event_bus = EventBus()
    shutdown_received = []

    async def on_shutdown(event_type: str, **kwargs):
        shutdown_received.append(kwargs)

    await event_bus.subscribe("safety.shutdown", on_shutdown)

    guard = ResourceGuard(
        event_bus=event_bus,
        cpu_critical=90,
        ram_critical_mb=750,
        check_interval=0.01,
    )

    # Mock high CPU
    with patch("psutil.cpu_percent", return_value=95.0), \
         patch("psutil.Process") as mock_proc:
        mock_proc_instance = MagicMock()
        mock_proc_instance.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_proc.return_value = mock_proc_instance

        guard.start()
        await asyncio.sleep(0.05)
        await guard.stop()

    assert len(shutdown_received) > 0
    assert shutdown_received[0]["reason"] == "CPU overload"


def test_cleanup_tts_temp_files(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()

    # Create dummy tts files
    (temp_dir / "tts_12345.mp3").write_text("audio")
    (temp_dir / "tts_67890.mp3").write_text("audio")
    (temp_dir / "other.txt").write_text("text")

    cleaned = cleanup_tts_temp_files(str(temp_dir))
    assert cleaned == 2
    assert (temp_dir / "other.txt").exists()
    assert not (temp_dir / "tts_12345.mp3").exists()
