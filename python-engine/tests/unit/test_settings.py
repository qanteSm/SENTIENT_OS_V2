"""Unit tests for Settings and configuration management."""

import os
from src.config.settings import Settings, get_settings


def test_default_settings():
    settings = Settings()
    assert settings.ws_host == "127.0.0.1"
    assert settings.intensity in ["mild", "medium", "extreme"]
    assert settings.language == "tr"
    assert settings.kill_switch_enabled is True


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("SENTIENT_WS_PORT", "9999")
    monkeypatch.setenv("SENTIENT_INTENSITY", "extreme")
    monkeypatch.setenv("SENTIENT_LANGUAGE", "en")

    settings = Settings()
    assert settings.ws_port == 9999
    assert settings.intensity == "extreme"
    assert settings.language == "en"


def test_get_settings_factory():
    settings = get_settings(intensity="mild", ws_port=5555)
    assert settings.intensity == "mild"
    assert settings.ws_port == 5555
