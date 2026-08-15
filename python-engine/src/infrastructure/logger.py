"""Structured JSON logging for SENTIENT_OS v2."""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def __init__(self, default_session_id: str = ""):
        super().__init__()
        self.default_session_id = default_session_id

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.datetime.fromtimestamp(
            record.created, datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S")

        session_id = getattr(record, "session_id", self.default_session_id)

        log_data: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "module": getattr(record, "module_name", record.name),
            "message": record.getMessage(),
            "session_id": session_id,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Allow passing extra custom fields
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


_configured_log_dir: Optional[str] = None
_current_session_id: str = ""


def set_global_session_id(session_id: str) -> None:
    """Update global session ID for all loggers."""
    global _current_session_id
    _current_session_id = session_id


def setup_logging(log_dir: str = "logs/", level: int = logging.INFO) -> None:
    """Initialize root log directory and file handler."""
    global _configured_log_dir
    _configured_log_dir = log_dir

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "sentient.log"

    root_logger = logging.getLogger("sentient")
    root_logger.setLevel(level)

    # Avoid duplicate handlers
    if not root_logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)


def get_logger(module_name: str, session_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Get a contextual logger adapter for a module."""
    if _configured_log_dir is None:
        setup_logging()

    base_logger = logging.getLogger(f"sentient.{module_name}")

    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
            extra = kwargs.setdefault("extra", {})
            extra["module_name"] = module_name
            extra["session_id"] = session_id or _current_session_id
            return msg, kwargs

    return ContextAdapter(base_logger, {})
