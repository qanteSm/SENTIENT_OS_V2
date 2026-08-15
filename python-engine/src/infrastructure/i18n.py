"""Internationalization (i18n) loader for SENTIENT_OS v2."""

import json
from pathlib import Path
from typing import Any, Optional
from src.infrastructure.logger import get_logger

logger = get_logger("i18n")


class I18n:
    """Loads and translates locale strings."""

    def __init__(self, language: str = "tr"):
        self.language = language
        self._translations: dict[str, Any] = {}
        self.load(language)

    def load(self, language: str) -> None:
        self.language = language
        locales_dir = Path(__file__).parent.parent / "locales"
        file_path = locales_dir / f"{language}.json"

        if not file_path.exists():
            file_path = locales_dir / "tr.json"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            logger.info(f"Loaded locale: '{language}'")
        except Exception as e:
            logger.error(f"Failed to load translations for '{language}': {e}")
            self._translations = {}

    def t(self, key_path: str, default: str = "") -> str:
        """Fetch nested key e.g. 'onboarding.welcome_title'."""
        keys = key_path.split(".")
        current = self._translations
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default or key_path
        return str(current)
