from __future__ import annotations

import re
from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from backend.app.domain import (
    Conversation,
    Galaxy,
    Memory,
    Message,
    Topic,
    Workspace,
    approximate_tokens,
    new_id,
    utc_now,
)
from backend.app.models import MemoryType


class MemoryRepository(Protocol):
    def ensure_workspace(self, workspace_id: str, name: str | None = None) -> Workspace: ...
    def get_or_create_conversation(self, workspace_id: str, external_id: str, source: str) -> Conversation: ...
    def find_message(self, workspace_id: str, source: str, external_id: str) -> Message | None: ...
    def create_message(self, message: Message) -> Message: ...
    def update_message_status(self, message_id: str, status: str) -> None: ...
    def get_or_create_galaxy(self, workspace_id: str, name: str, description: str) -> Galaxy: ...
    def list_topics(self, workspace_id: str) -> list[Topic]: ...
    def get_topic(self, workspace_id: str, topic_id: str) -> Topic | None: ...
    def find_topic_by_id(self, workspace_id: str, topic_id: str) -> Topic | None: ...
    def create_topic(self, topic: Topic) -> Topic: ...
    def create_memory(self, memory: Memory) -> Memory: ...
    def list_memories_for_message(self, message_id: str) -> list[Memory]: ...
    def list_memories_for_topic(self, workspace_id: str, topic_id: str) -> list[Memory]: ...
    def search_memories(self, workspace_id: str, query: str, topic_ids: list[str], limit: int) -> list[Memory]: ...
    def reset_workspace(self, workspace_id: str) -> None: ...


class PostgresMemoryRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def ensure_workspace(self, workspace_id: str, name: str | None = None) -> Workspace:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO workspaces (id, name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET name = workspaces.name
                RETURNING *
                """,
                (workspace_id, name or workspace_id, now),
            ).fetchone()
        return _workspace(row)

    def get_or_create_conversation(self, workspace_id: str, external_id: str, source: str) -> Conversation:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO conversations (id, workspace_id, external_id, source, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (workspace_id, source, external_id) DO UPDATE SET source = EXCLUDED.source
                RETURNING *
                """,
                (new_id(), workspace_id, external_id, source, now),
            ).fetchone()
        return _conversation(row)

    def find_message(self, workspace_id: str, source: str, external_id: str) -> Message | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM messages WHERE workspace_id = %s AND source = %s AND external_id = %s",
                (workspace_id, source, external_id),
            ).fetchone()
        return _message(row) if row else None

    def create_message(self, message: Message) -> Message:
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO messages (
                    id, workspace_id, conversation_id, external_id, role, content, source,
                    source_url, created_at, processed_at, processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    message.id,
                    message.workspace_id,
                    message.conversation_id,
                    message.external_id,
                    message.role,
                    message.content,
                    message.source,
                    message.source_url,
                    message.created_at,
                    message.processed_at,
                    message.processing_status,
                ),
            ).fetchone()
        return _message(row)

    def update_message_status(self, message_id: str, status: str) -> None:
        processed_at = utc_now() if status in {"processed", "failed"} else None
        with self._connect() as conn:
            conn.execute(
                "UPDATE messages SET processing_status = %s, processed_at = %s WHERE id = %s",
                (status, processed_at, message_id),
            )

    def get_or_create_galaxy(self, workspace_id: str, name: str, description: str) -> Galaxy:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO galaxies (id, workspace_id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (workspace_id, name) DO UPDATE
                SET description = COALESCE(NULLIF(galaxies.description, ''), EXCLUDED.description),
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                (new_id(), workspace_id, name, description, now, now),
            ).fetchone()
        return _galaxy(row)

    def list_topics(self, workspace_id: str) -> list[Topic]:
        with self._connect() as conn:
            rows = conn.execute(_TOPICS_SQL + " WHERE t.workspace_id = %s ORDER BY t.updated_at DESC", (workspace_id,)).fetchall()
        return [_topic(row) for row in rows]

    def get_topic(self, workspace_id: str, topic_id: str) -> Topic | None:
        with self._connect() as conn:
            row = conn.execute(_TOPICS_SQL + " WHERE t.workspace_id = %s AND t.id = %s", (workspace_id, topic_id)).fetchone()
        return _topic(row) if row else None

    def find_topic_by_id(self, workspace_id: str, topic_id: str) -> Topic | None:
        return self.get_topic(workspace_id, topic_id)

    def create_topic(self, topic: Topic) -> Topic:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO topics (id, workspace_id, galaxy_id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (workspace_id, galaxy_id, name) DO UPDATE
                SET description = COALESCE(NULLIF(topics.description, ''), EXCLUDED.description),
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                (topic.id, topic.workspace_id, topic.galaxy_id, topic.name, topic.description, now, now),
            ).fetchone()
            full = conn.execute(_TOPICS_SQL + " WHERE t.id = %s", (row["id"],)).fetchone()
        return _topic(full)

    def create_memory(self, memory: Memory) -> Memory:
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO memories (
                    id, workspace_id, topic_id, message_id, content, memory_type, confidence, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    memory.id,
                    memory.workspace_id,
                    memory.topic_id,
                    memory.message_id,
                    memory.content,
                    memory.memory_type.value,
                    memory.confidence,
                    memory.created_at,
                ),
            ).fetchone()
            full = conn.execute(_MEMORIES_SQL + " WHERE m.id = %s", (row["id"],)).fetchone()
        return _memory(full)

    def list_memories_for_message(self, message_id: str) -> list[Memory]:
        with self._connect() as conn:
            rows = conn.execute(_MEMORIES_SQL + " WHERE m.message_id = %s ORDER BY m.created_at", (message_id,)).fetchall()
        return [_memory(row) for row in rows]

    def list_memories_for_topic(self, workspace_id: str, topic_id: str) -> list[Memory]:
        with self._connect() as conn:
            rows = conn.execute(
                _MEMORIES_SQL + " WHERE m.workspace_id = %s AND m.topic_id = %s ORDER BY m.created_at DESC",
                (workspace_id, topic_id),
            ).fetchall()
        return [_memory(row) for row in rows]

    def search_memories(self, workspace_id: str, query: str, topic_ids: list[str], limit: int) -> list[Memory]:
        # OR the query terms: a natural-language question must retrieve any memory
        # matching some of its words (ranked), not only memories containing all of
        # them — grounding filtering is the LLM's job, not retrieval's.
        terms = re.findall(r"[A-Za-z0-9]+", query)
        if not terms:
            return []
        ts_query = " | ".join(terms)
        params: list[object] = [workspace_id, ts_query]
        topic_clause = ""
        if topic_ids:
            topic_clause = " AND m.topic_id = ANY(%s)"
            params.append(topic_ids)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                _MEMORIES_SQL
                + f"""
                WHERE m.workspace_id = %s
                  AND to_tsvector('english', m.content) @@ to_tsquery('english', %s)
                  {topic_clause}
                ORDER BY ts_rank(to_tsvector('english', m.content), to_tsquery('english', %s)) DESC,
                         m.created_at DESC
                LIMIT %s
                """,
                tuple(params[:-1] + [ts_query, params[-1]]),
            ).fetchall()
        return [_memory(row) for row in rows]

    def reset_workspace(self, workspace_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM workspaces WHERE id = %s", (workspace_id,))


_TOPICS_SQL = """
SELECT t.*, g.name AS galaxy_name, (
  SELECT COUNT(*) FROM memories m WHERE m.topic_id = t.id
)::int AS memory_count
FROM topics t
JOIN galaxies g ON g.id = t.galaxy_id
"""

_MEMORIES_SQL = """
SELECT m.*, t.name AS topic_name, msg.source, msg.source_url, msg.created_at AS source_timestamp
FROM memories m
JOIN topics t ON t.id = m.topic_id
JOIN messages msg ON msg.id = m.message_id
"""


def _workspace(row) -> Workspace:
    return Workspace(id=row["id"], name=row["name"], created_at=row["created_at"])


def _conversation(row) -> Conversation:
    return Conversation(id=row["id"], workspace_id=row["workspace_id"], external_id=row["external_id"], source=row["source"], created_at=row["created_at"])


def _message(row) -> Message:
    return Message(
        id=row["id"],
        workspace_id=row["workspace_id"],
        conversation_id=row["conversation_id"],
        external_id=row["external_id"],
        role=row["role"],
        content=row["content"],
        source=row["source"],
        source_url=row["source_url"],
        created_at=row["created_at"],
        processed_at=row["processed_at"],
        processing_status=row["processing_status"],
    )


def _galaxy(row) -> Galaxy:
    return Galaxy(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _topic(row) -> Topic:
    return Topic(
        id=row["id"],
        workspace_id=row["workspace_id"],
        galaxy_id=row["galaxy_id"],
        galaxy_name=row["galaxy_name"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        memory_count=row["memory_count"],
    )


def _memory(row) -> Memory:
    return Memory(
        id=row["id"],
        workspace_id=row["workspace_id"],
        topic_id=row["topic_id"],
        topic_name=row["topic_name"],
        message_id=row["message_id"],
        content=row["content"],
        memory_type=MemoryType(row["memory_type"]),
        confidence=float(row["confidence"]),
        created_at=row["created_at"],
        source=row["source"],
        source_url=row["source_url"],
        source_timestamp=row["source_timestamp"],
        approximate_token_count=approximate_tokens(row["content"]),
    )
