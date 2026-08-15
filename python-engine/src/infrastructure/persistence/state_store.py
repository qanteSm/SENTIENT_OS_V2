"""StateStore repository for sessions, memory, checkpoints, and event logs."""

import datetime
import json
from typing import Any, Optional
from .database import DatabaseManager


class StateStore:
    """Provides high-level CRUD operations for application state and memories."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _now_iso(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Session Operations ---

    async def create_session(
        self,
        session_id: str,
        language: str = "tr",
        intensity: str = "medium",
        current_phase: int = 1,
    ) -> dict[str, Any]:
        started_at = self._now_iso()
        async with self.db.connection.execute(
            """
            INSERT INTO sessions (id, started_at, current_phase, language, intensity, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (session_id, started_at, current_phase, language, intensity),
        ):
            await self.db.connection.commit()

        return {
            "id": session_id,
            "started_at": started_at,
            "current_phase": current_phase,
            "language": language,
            "intensity": intensity,
            "status": "active",
        }

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        async with self.db.connection.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def update_session(self, session_id: str, **kwargs: Any) -> bool:
        if not kwargs:
            return False

        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(session_id)

        query = f"UPDATE sessions SET {', '.join(fields)} WHERE id = ?"
        async with self.db.connection.execute(query, tuple(values)):
            await self.db.connection.commit()
        return True

    async def get_active_sessions(self) -> list[dict[str, Any]]:
        async with self.db.connection.execute(
            "SELECT * FROM sessions WHERE status = 'active'"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Working Memory ---

    async def add_working_memory(
        self, session_id: str, role: str, content: str
    ) -> int:
        ts = self._now_iso()
        async with self.db.connection.execute(
            """
            INSERT INTO working_memory (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, ts),
        ) as cursor:
            await self.db.connection.commit()
            return cursor.lastrowid

    async def get_working_memory(
        self, session_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        async with self.db.connection.execute(
            """
            SELECT * FROM (
                SELECT * FROM working_memory
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Episodic Memory ---

    async def add_episodic_memory(
        self, session_id: str, summary: str, importance: float = 0.5
    ) -> int:
        ts = self._now_iso()
        async with self.db.connection.execute(
            """
            INSERT INTO episodic_memory (session_id, summary, importance, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, summary, importance, ts),
        ) as cursor:
            await self.db.connection.commit()
            return cursor.lastrowid

    async def get_episodic_memory(
        self, session_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        async with self.db.connection.execute(
            """
            SELECT * FROM episodic_memory
            WHERE session_id = ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # --- Checkpoints ---

    async def save_checkpoint(
        self, session_id: str, label: str, state: dict[str, Any]
    ) -> int:
        ts = self._now_iso()
        state_json = json.dumps(state, ensure_ascii=False)
        async with self.db.connection.execute(
            """
            INSERT INTO checkpoints (session_id, label, state_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, label, state_json, ts),
        ) as cursor:
            await self.db.connection.commit()
            return cursor.lastrowid

    async def get_latest_checkpoint(
        self, session_id: str
    ) -> Optional[dict[str, Any]]:
        async with self.db.connection.execute(
            """
            SELECT * FROM checkpoints
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data["state"] = json.loads(data["state_json"])
                return data
            return None

    # --- User Profile (Semantic Memory) ---

    async def set_profile_value(self, key: str, value: Any) -> None:
        ts = self._now_iso()
        val_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        async with self.db.connection.execute(
            """
            INSERT INTO user_profile (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, val_str, ts),
        ):
            await self.db.connection.commit()

    async def get_profile_dict(self) -> dict[str, Any]:
        async with self.db.connection.execute("SELECT key, value FROM user_profile") as cursor:
            rows = await cursor.fetchall()
            res = {}
            for r in rows:
                k, v = r["key"], r["value"]
                try:
                    res[k] = json.loads(v)
                except Exception:
                    res[k] = v
            return res

    # --- Event Log ---

    async def log_event(
        self, session_id: str, event_type: str, payload: Optional[dict[str, Any]] = None
    ) -> int:
        ts = self._now_iso()
        payload_json = json.dumps(payload, ensure_ascii=False) if payload else None
        async with self.db.connection.execute(
            """
            INSERT INTO event_log (session_id, event_type, payload_json, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, event_type, payload_json, ts),
        ) as cursor:
            await self.db.connection.commit()
            return cursor.lastrowid
