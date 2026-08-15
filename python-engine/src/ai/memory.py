"""Three-tier memory architecture (Working, Episodic, Semantic) for SENTIENT_OS v2."""

import datetime
from typing import Any, Callable, List, Optional
from src.ai.response_parser import Episode, Message
from src.infrastructure.logger import get_logger
from src.infrastructure.persistence.state_store import StateStore

logger = get_logger("memory")


class Memory:
    """Manages Working Memory (RAM FIFO), Episodic Memory (Summaries), and Semantic Memory (User Profile)."""

    def __init__(
        self,
        session_id: str,
        state_store: Optional[StateStore] = None,
        working_memory_limit: int = 20,
        episodic_trigger_interval: int = 10,
        summary_generator: Optional[Callable[[List[Message]], Any]] = None,
    ):
        self.session_id = session_id
        self.state_store = state_store
        self.working_memory_limit = working_memory_limit
        self.episodic_trigger_interval = episodic_trigger_interval
        self.summary_generator = summary_generator

        # In-memory working memory cache (FIFO)
        self._working_memory: List[Message] = []
        self._message_counter = 0

    def _now_iso(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Working Memory ---

    async def add_message(
        self, role: str, content: str, emotion: str = "calm"
    ) -> Message:
        """Add a message to working memory (FIFO max limit) and persist to SQLite."""
        ts = self._now_iso()
        msg = Message(role=role, content=content, timestamp=ts, emotion=emotion)

        self._working_memory.append(msg)
        if len(self._working_memory) > self.working_memory_limit:
            self._working_memory.pop(0)

        self._message_counter += 1

        # Persist to database if available
        if self.state_store:
            try:
                await self.state_store.add_working_memory(
                    session_id=self.session_id, role=role, content=content
                )
            except Exception as e:
                logger.error(f"Failed to persist working memory: {e}")

        # Check if episodic generation trigger reached
        if (
            self._message_counter > 0
            and self._message_counter % self.episodic_trigger_interval == 0
            and self.summary_generator is not None
        ):
            try:
                await self.generate_episode()
            except Exception as e:
                logger.error(f"Failed to generate episodic memory: {e}")

        return msg

    def get_working_memory(self) -> List[Message]:
        """Return the current active working memory list."""
        return list(self._working_memory)

    async def load_working_memory(self) -> None:
        """Load recent messages from SQLite into working memory."""
        if not self.state_store:
            return
        rows = await self.state_store.get_working_memory(
            self.session_id, limit=self.working_memory_limit
        )
        self._working_memory = [
            Message(
                role=r["role"],
                content=r["content"],
                timestamp=r["timestamp"],
            )
            for r in rows
        ]

    # --- Episodic Memory ---

    async def generate_episode(self) -> Optional[Episode]:
        """Generate and store an episodic summary of recent messages."""
        if not self.summary_generator or not self._working_memory:
            return None

        logger.info("Triggering episodic memory summary generation...")
        recent_messages = list(self._working_memory)
        summary = await self.summary_generator(recent_messages)
        if not summary or not summary.strip():
            return None

        ts = self._now_iso()
        ep_id = 0
        if self.state_store:
            ep_id = await self.state_store.add_episodic_memory(
                session_id=self.session_id,
                summary=summary.strip(),
                importance=0.7,
            )

        episode = Episode(
            id=ep_id,
            summary=summary.strip(),
            importance=0.7,
            created_at=ts,
        )
        logger.info(f"Episodic memory generated: {summary[:60]}...")
        return episode

    async def get_recent_episodes(self, limit: int = 10) -> List[Episode]:
        """Retrieve recent episodic memories from SQLite."""
        if not self.state_store:
            return []

        rows = await self.state_store.get_episodic_memory(
            self.session_id, limit=limit
        )
        return [
            Episode(
                id=r["id"],
                summary=r["summary"],
                importance=r["importance"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # --- Semantic Memory (User Profile) ---

    async def get_profile(self) -> dict[str, Any]:
        """Retrieve semantic memory user profile."""
        if not self.state_store:
            return {}
        return await self.state_store.get_profile_dict()

    async def update_profile_entry(self, key: str, value: Any) -> None:
        """Update a specific attribute in semantic memory."""
        if self.state_store:
            await self.state_store.set_profile_value(key, value)
            logger.debug(f"User profile updated: {key}={value}")
