"""Unit tests for Timeline pacing and event scheduler."""

import asyncio
import pytest
from src.core.event_bus import EventBus
from src.story.narrative import NarrativePhase
from src.story.scenes.first_contact import SceneEvent
from src.story.timeline import Timeline


def test_pacing_delays():
    bus = EventBus()
    timeline = Timeline(event_bus=bus, base_interval=30.0)

    # Active user: 30 * 1.5 = 45s
    timeline.set_idle_state(is_idle=False)
    assert timeline.calculate_next_delay() == 45.0

    # Idle user (>30s): 30 * 0.6 = 18s
    timeline.set_idle_state(is_idle=True, idle_seconds=40.0)
    assert timeline.calculate_next_delay() == 18.0


@pytest.mark.asyncio
async def test_timeline_event_dispatch():
    bus = EventBus()
    dispatched_effects = []

    async def on_effect(event_type: str, **kwargs):
        dispatched_effects.append(kwargs.get("payload"))

    await bus.subscribe("effect", on_effect)

    events = [
        SceneEvent(
            time_offset_s=0.01,
            effects=[{"type": "mouse_drift", "params": {"intensity": 0.1}}],
            description="Test drift",
        ),
        SceneEvent(
            time_offset_s=0.02,
            effects=[{"type": "screen_shake", "params": {"intensity": 0.2}}],
            description="Test shake",
        ),
    ]

    timeline = Timeline(event_bus=bus, events=events, base_interval=0.01)
    await timeline.start_phase(NarrativePhase.FIRST_CONTACT)

    await asyncio.sleep(0.08)
    await timeline.stop()

    assert len(dispatched_effects) >= 2
    effect_names = [e.get("name") for e in dispatched_effects]
    assert "mouse_drift" in effect_names
    assert "screen_shake" in effect_names
