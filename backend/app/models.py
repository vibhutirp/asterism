from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    fact = "fact"
    idea = "idea"
    decision = "decision"
    question = "question"
    task = "task"
    preference = "preference"
    observation = "observation"


class MessageIngestRequest(BaseModel):
    workspace_id: str = Field(alias="workspaceId")
    conversation_id: str = Field(alias="conversationId")
    external_id: str = Field(alias="externalId")
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)
    source: str
    source_url: str | None = Field(default=None, alias="sourceUrl")


class IngestedMemory(BaseModel):
    id: str
    topic_id: str = Field(alias="topicId")
    topic_name: str = Field(alias="topicName")
    content: str
    memory_type: MemoryType = Field(alias="memoryType")
    confidence: float


class MessageIngestResponse(BaseModel):
    message_id: str = Field(alias="messageId")
    status: str
    duplicate: bool
    memories_created: int = Field(alias="memoriesCreated")
    topics_created: int = Field(alias="topicsCreated")
    topics_reused: int = Field(alias="topicsReused")
    memories: list[IngestedMemory]


class GalaxyOut(BaseModel):
    id: str
    name: str


class TopicOut(BaseModel):
    id: str
    name: str
    description: str
    galaxy: GalaxyOut
    memory_count: int = Field(alias="memoryCount")


class TopicsResponse(BaseModel):
    topics: list[TopicOut]


class MemorySource(BaseModel):
    message_id: str = Field(alias="messageId")
    source: str
    source_url: str | None = Field(alias="sourceUrl")
    timestamp: datetime


class MemoryOut(BaseModel):
    id: str
    topic_id: str = Field(alias="topicId")
    topic_name: str = Field(alias="topicName")
    content: str
    memory_type: MemoryType = Field(alias="memoryType")
    confidence: float
    created_at: datetime = Field(alias="createdAt")
    source: MemorySource
    approximate_token_count: int = Field(alias="approximateTokenCount")


class TopicDetailResponse(BaseModel):
    topic: TopicOut
    galaxy: GalaxyOut
    memory_count: int = Field(alias="memoryCount")
    overview: str
    memories: list[MemoryOut]


class QueryRequest(BaseModel):
    workspace_id: str = Field(default="demo", alias="workspaceId")
    query: str = Field(min_length=1)
    max_context_tokens: int = Field(default=2000, alias="maxContextTokens", ge=1, le=12000)
    topic_ids: list[str] = Field(default_factory=list, alias="topicIds")
    target_model: str | None = Field(default=None, alias="targetModel")


class ContextMetadata(BaseModel):
    used_tokens: int = Field(alias="usedTokens")
    max_context_tokens: int = Field(alias="maxContextTokens")
    memories: list[MemoryOut]


class QueryResponse(BaseModel):
    answer: str
    insufficient_context: bool = Field(alias="insufficientContext")
    context: ContextMetadata
    supporting_memories: list[MemoryOut] = Field(alias="supportingMemories")


class ResetDemoResponse(BaseModel):
    workspace_id: str = Field(alias="workspaceId")
    topics_created: int = Field(alias="topicsCreated")
    memories_created: int = Field(alias="memoriesCreated")
