from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.models import MemoryType


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def approximate_tokens(text: str) -> int:
    return max(1, len(text.split()))


@dataclass(frozen=True)
class Workspace:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class Conversation:
    id: str
    workspace_id: str
    external_id: str
    source: str
    created_at: datetime


@dataclass(frozen=True)
class Message:
    id: str
    workspace_id: str
    conversation_id: str
    external_id: str
    role: str
    content: str
    source: str
    source_url: str | None
    created_at: datetime
    processed_at: datetime | None
    processing_status: str


@dataclass(frozen=True)
class Galaxy:
    id: str
    workspace_id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Topic:
    id: str
    workspace_id: str
    galaxy_id: str
    galaxy_name: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    memory_count: int = 0


@dataclass(frozen=True)
class Memory:
    id: str
    workspace_id: str
    topic_id: str
    topic_name: str
    message_id: str
    content: str
    memory_type: MemoryType
    confidence: float
    created_at: datetime
    source: str
    source_url: str | None
    source_timestamp: datetime
    approximate_token_count: int


@dataclass(frozen=True)
class ExtractedMemory:
    content: str
    memory_type: MemoryType
    confidence: float
    suggested_topic_name: str
    suggested_topic_description: str
    suggested_galaxy_name: str
    suggested_galaxy_description: str
