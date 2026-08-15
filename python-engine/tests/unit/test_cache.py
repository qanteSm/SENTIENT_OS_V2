"""Unit tests for ResponseCache."""

import time
from src.ai.cache import ResponseCache
from src.ai.response_parser import AIResponse


def test_cache_hit_and_miss():
    cache = ResponseCache(default_ttl=10.0)
    resp = AIResponse(speech="Önbellek yanıtı", emotion="calm")

    # Miss
    assert cache.get("merhaba", phase=1, emotion="calm") is None

    # Set
    cache.set("merhaba", phase=1, emotion="calm", response=resp)

    # Hit
    cached = cache.get("merhaba", phase=1, emotion="calm")
    assert cached is not None
    assert cached.speech == "Önbellek yanıtı"

    # Miss with different phase or emotion
    assert cache.get("merhaba", phase=2, emotion="calm") is None
    assert cache.get("merhaba", phase=1, emotion="angry") is None


def test_cache_expiration():
    cache = ResponseCache(default_ttl=0.05)
    resp = AIResponse(speech="Geçici yanıt", emotion="calm")

    cache.set("test", phase=1, emotion="calm", response=resp)
    assert cache.get("test", phase=1, emotion="calm") is not None

    time.sleep(0.06)
    # Should be expired
    assert cache.get("test", phase=1, emotion="calm") is None
