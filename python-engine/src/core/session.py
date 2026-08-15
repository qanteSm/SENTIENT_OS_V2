"""Session lifecycle management and checkpointing for SENTIENT_OS v2."""

import datetime
import time
from typing import Any, Optional
from src.infrastructure.logger import get_logger
from src.infrastructure.persistence.state_store import StateStore
from src.story.narrative import NarrativeState, NarrativeStateMachine

logger = get_logger("session")


class SessionManager:
    """Manages active session lifecycle, save checkpoints, and crash recovery."""

    def __init__(self, state_store: StateStore, session_id: str):
        self.state_store = state_store
        self.session_id = session_id
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    async def initialize(
        self, language: str = "tr", intensity: str = "medium"
    ) -> dict[str, Any]:
        """Initialize or resume session in database."""
        session_data = await self.state_store.get_session(self.session_id)
        if not session_data:
            session_data = await self.state_store.create_session(
                session_id=self.session_id,
                language=language,
                intensity=intensity,
            )
            logger.info(f"New session initialized: {self.session_id}")
        else:
            logger.info(f"Existing session resumed: {self.session_id}")

        self._is_active = True
        return session_data

    async def save_checkpoint(
        self,
        label: str,
        narrative_state: NarrativeState,
        personality_dict: Optional[dict[str, Any]] = None,
    ) -> int:
        """Save a snapshot checkpoint of the current game and narrative state."""
        state_payload = {
            "session_id": self.session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "narrative": narrative_state.to_dict(),
            "personality": personality_dict or {},
        }
        cp_id = await self.state_store.save_checkpoint(
            session_id=self.session_id, label=label, state=state_payload
        )
        logger.info(f"Checkpoint saved: label='{label}', id={cp_id}")
        return cp_id

    async def load_latest_checkpoint(self) -> Optional[dict[str, Any]]:
        """Load latest checkpoint if resuming."""
        return await self.state_store.get_latest_checkpoint(self.session_id)

    async def end_session(self, status: str = "completed") -> None:
        """Close session cleanly."""
        self._is_active = False
        ended_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.state_store.update_session(
            self.session_id, status=status, ended_at=ended_at
        )
        logger.info(f"Session {self.session_id} ended with status='{status}'")

    @classmethod
    async def check_crash_recovery(cls, state_store: StateStore) -> list[dict[str, Any]]:
        """Check for unclosed active sessions from past crashes."""
        active = await state_store.get_active_sessions()
        if active:
            logger.warning(f"Found {len(active)} crashed active session(s) from previous runs.")
            for sess in active:
                await state_store.update_session(sess["id"], status="crashed")
        return active
