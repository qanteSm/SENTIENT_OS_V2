"""Semantic response cache for SENTIENT_OS v2 AI engine."""

import hashlib
import time
from typing import Dict, Optional, Tuple
from src.ai.response_parser import AIResponse
from src.infrastructure.logger import get_logger

logger = get_logger("cache")


class ResponseCache:
    """In-memory cache for AI responses with TTL expiration."""

    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[AIResponse, float]] = {}

    def _generate_key(self, user_input: str, phase: int, emotion: str) -> str:
        raw = f"{user_input.strip().lower()}|{phase}|{emotion.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, user_input: str, phase: int, emotion: str) -> Optional[AIResponse]:
        """Retrieve cached response if key exists and has not expired."""
        key = self._generate_key(user_input, phase, emotion)
        if key not in self._cache:
            return None

        response, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for key {key[:8]} (input='{user_input[:30]}')")
        return response

    def set(
        self,
        user_input: str,
        phase: int,
        emotion: str,
        response: AIResponse,
        ttl: Optional[float] = None,
    ) -> None:
        """Cache an AIResponse with expiration."""
        key = self._generate_key(user_input, phase, emotion)
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = (response, expiry)
        logger.debug(f"Cached response for key {key[:8]}")

    def clear(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()

    def prune_expired(self) -> int:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired_keys:
            del self._cache[k]
        return len(expired_keys)

    def size(self) -> int:
        return len(self._cache)
