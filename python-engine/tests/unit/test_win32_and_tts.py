"""Unit tests for EdgeTTS, Win32 controllers, and Keyboard panic detection."""

import os
import pytest
from src.core.event_bus import EventBus
from src.infrastructure.edge_tts import EdgeTTSWorker
from src.infrastructure.platform.windows.brightness import WindowsBrightnessManager
from src.infrastructure.platform.windows.keyboard import KeyboardPanicDetector
from src.infrastructure.platform.windows.mouse import WindowsMouseController
from src.infrastructure.platform.windows.notifications import NotificationManager
from src.infrastructure.platform.windows.wallpaper import WindowsWallpaperManager


@pytest.mark.asyncio
async def test_edge_tts_generation(tmp_path):
    temp_dir = str(tmp_path / "tts_temp")
    worker = EdgeTTSWorker(temp_dir=temp_dir)

    # Empty text returns None
    res = await worker.generate_speech("")
    assert res is None

    # Normal generation
    res = await worker.generate_speech("Merhaba", profile="whisper")
    if res:
        assert os.path.exists(res)
        assert res.endswith(".mp3")


def test_mouse_controller():
    mouse = WindowsMouseController()
    x, y = mouse.get_cursor_pos()
    assert isinstance(x, int)
    assert isinstance(y, int)


def test_wallpaper_and_brightness():
    wp = WindowsWallpaperManager()
    assert wp._original_wallpaper is not None or wp._user32 is not None

    bm = WindowsBrightnessManager()
    assert bm._original_brightness is None or isinstance(bm._original_brightness, int)


@pytest.mark.asyncio
async def test_keyboard_panic_detector():
    bus = EventBus()
    panic_events = []

    async def on_panic(event_type: str, **kwargs):
        panic_events.append(kwargs.get("trigger"))

    await bus.subscribe("safety.panic_detected", on_panic)

    detector = KeyboardPanicDetector(event_bus=bus)

    # Trigger 5 ESC presses in short succession
    for _ in range(5):
        await detector.record_esc_pressed()

    assert len(panic_events) == 1
    assert panic_events[0] == "esc_spam"


@pytest.mark.asyncio
async def test_notification_manager():
    bus = EventBus()
    dispatched = []

    async def on_effect(event_type: str, **kwargs):
        dispatched.append(kwargs.get("payload"))

    await bus.subscribe("effect", on_effect)

    mgr = NotificationManager(event_bus=bus)
    await mgr.show_notification(title="Test", body="Body text")

    assert len(dispatched) == 1
    assert dispatched[0]["name"] == "fake_notification"
    assert dispatched[0]["params"]["title"] == "Test"
