"""Unit tests for EventBus pub/sub, multiple subscribers, and error isolation."""

import asyncio
import pytest
from src.core.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = EventBus()
    received = []

    async def on_test(event_type: str, data: str):
        received.append((event_type, data))

    await bus.subscribe("test.event", on_test)
    await bus.publish("test.event", data="hello_world")

    assert len(received) == 1
    assert received[0] == ("test.event", "hello_world")


@pytest.mark.asyncio
async def test_multiple_subscribers():
    bus = EventBus()
    results = []

    async def sub1(event_type: str, value: int):
        results.append(value * 2)

    async def sub2(event_type: str, value: int):
        results.append(value * 3)

    await bus.subscribe("calc", sub1)
    await bus.subscribe("calc", sub2)

    await bus.publish("calc", value=10)

    assert set(results) == {20, 30}


@pytest.mark.asyncio
async def test_unsubscribe():
    bus = EventBus()
    calls = []

    async def callback(event_type: str, **kwargs):
        calls.append(1)

    await bus.subscribe("ping", callback)
    await bus.publish("ping")
    assert len(calls) == 1

    await bus.unsubscribe("ping", callback)
    await bus.publish("ping")
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_error_isolation():
    bus = EventBus()
    success_called = []

    async def faulty_subscriber(event_type: str, **kwargs):
        raise ValueError("Simulated subscriber error")

    async def good_subscriber(event_type: str, **kwargs):
        success_called.append(True)

    await bus.subscribe("action", faulty_subscriber)
    await bus.subscribe("action", good_subscriber)

    # Should not raise exception
    await bus.publish("action")
    assert len(success_called) == 1
