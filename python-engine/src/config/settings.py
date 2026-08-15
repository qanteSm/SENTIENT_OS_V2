"""Pydantic settings configuration for SENTIENT_OS v2."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class Settings(BaseSettings):
    """Application settings loaded from defaults, environment variables, and .env file."""

    # API
    gemini_api_key: str = ""

    # Server
    ws_host: str = "127.0.0.1"
    ws_port: int = 0  # 0 = random port

    # Safety
    kill_switch_enabled: bool = True
    cpu_critical: int = 90
    ram_critical_mb: int = 750

    # Horror
    intensity: str = "medium"  # mild, medium, extreme
    language: str = "tr"

    # TTS
    tts_voice: str = "tr-TR-AhmetNeural"

    # Paths
    db_path: str = "data/sentient.db"
    temp_dir: str = "temp/"
    log_dir: str = "logs/"

    model_config = SettingsConfigDict(
        env_prefix="SENTIENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_yaml_defaults(yaml_path: Optional[str | Path] = None) -> dict:
    """Load default configuration from YAML file if available."""
    if yaml_path is None:
        yaml_path = Path(__file__).parent / "defaults.yaml"
    else:
        yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        return {}

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        flattened = {}
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        flattened[sub_key] = sub_val
                else:
                    flattened[key] = val
        return flattened
    except Exception:
        return {}


def get_settings(
    env_file: Optional[str] = None, yaml_path: Optional[str | Path] = None, **kwargs
) -> Settings:
    """Create and return a Settings instance initialized with yaml defaults and env vars."""
    yaml_defaults = load_yaml_defaults(yaml_path)
    # Remove empty string values from yaml_defaults so they don't override .env or environment variables
    cleaned_defaults = {k: v for k, v in yaml_defaults.items() if v != "" and v is not None}
    merged = {**cleaned_defaults, **kwargs}

    # Locate .env file if not specified
    if env_file is None:
        # Check current working directory, python-engine root, and workspace root
        candidates = [
            Path(".env"),
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
        ]
        for candidate in candidates:
            if candidate.exists():
                env_file = str(candidate)
                break

    if env_file:
        return Settings(_env_file=env_file, **merged)
    return Settings(**merged)
