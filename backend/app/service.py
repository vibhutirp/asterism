from __future__ import annotations

from backend.app.domain import Message, Memory, Topic, approximate_tokens, new_id, utc_now
from backend.app.llm import LLMClient, TopicCandidate
from backend.app.models import (
    ContextMetadata,
    GalaxyOut,
    IngestedMemory,
    MemoryOut,
    MemorySource,
    MessageIngestRequest,
    MessageIngestResponse,
    QueryRequest,
    QueryResponse,
    ResetDemoResponse,
    TopicDetailResponse,
    TopicOut,
    TopicsResponse,
)
from backend.app.repository import MemoryRepository


class MemoryEngine:
    def __init__(self, repository: MemoryRepository, llm: LLMClient, default_context_tokens: int = 2000):
        self.repository = repository
        self.llm = llm
        self.default_context_tokens = default_context_tokens

    def ingest_message(self, payload: MessageIngestRequest) -> MessageIngestResponse:
        self.repository.ensure_workspace(payload.workspace_id, payload.workspace_id)
        existing = self.repository.find_message(payload.workspace_id, payload.source, payload.external_id)
        if existing is not None:
            memories = self.repository.list_memories_for_message(existing.id)
            return self._ingest_response(existing.id, existing.processing_status, True, memories, 0, 0)

        conversation = self.repository.get_or_create_conversation(
            payload.workspace_id,
            payload.conversation_id,
            payload.source,
        )
        message = self.repository.create_message(
            Message(
                id=new_id(),
                workspace_id=payload.workspace_id,
                conversation_id=conversation.id,
                external_id=payload.external_id,
                role=payload.role,
                content=payload.content,
                source=payload.source,
                source_url=payload.source_url,
                created_at=utc_now(),
                processed_at=None,
                processing_status="processing",
            )
        )

        try:
            extracted = self._extract_with_retry(payload.content)
            if not extracted:
                self.repository.update_message_status(message.id, "processed")
                return self._ingest_response(message.id, "processed", False, [], 0, 0)
            topics_created = 0
            topics_reused = 0
            memories: list[Memory] = []
            for item in extracted:
                topic, created = self._assign_topic(payload.workspace_id, item)
                topics_created += int(created)
                topics_reused += int(not created)
                memories.append(
                    self.repository.create_memory(
                        Memory(
                            id=new_id(),
                            workspace_id=payload.workspace_id,
                            topic_id=topic.id,
                            topic_name=topic.name,
                            message_id=message.id,
                            content=item.content,
                            memory_type=item.memory_type,
                            confidence=item.confidence,
                            created_at=utc_now(),
                            source=payload.source,
                            source_url=payload.source_url,
                            source_timestamp=message.created_at,
                            approximate_token_count=approximate_tokens(item.content),
                        )
                    )
                )
            self.repository.update_message_status(message.id, "processed")
            return self._ingest_response(message.id, "processed", False, memories, topics_created, topics_reused)
        except Exception:
            self.repository.update_message_status(message.id, "failed")
            raise

    def list_topics(self, workspace_id: str) -> TopicsResponse:
        return TopicsResponse(topics=[self._topic_out(topic) for topic in self.repository.list_topics(workspace_id)])

    def get_topic(self, workspace_id: str, topic_id: str) -> TopicDetailResponse | None:
        topic = self.repository.get_topic(workspace_id, topic_id)
        if topic is None:
            return None
        memories = self.repository.list_memories_for_topic(workspace_id, topic_id)
        galaxy = GalaxyOut(id=topic.galaxy_id, name=topic.galaxy_name)
        return TopicDetailResponse(
            topic=self._topic_out(topic),
            galaxy=galaxy,
            memoryCount=len(memories),
            overview=topic.description,
            memories=[self._memory_out(memory) for memory in memories],
        )

    def retrieve_context(self, request: QueryRequest) -> ContextMetadata:
        max_tokens = request.max_context_tokens or self.default_context_tokens
        memories = self.repository.search_memories(request.workspace_id, request.query, request.topic_ids, limit=50)
        selected: list[MemoryOut] = []
        used_tokens = 0
        seen: set[str] = set()
        for memory in memories:
            if memory.id in seen:
                continue
            if used_tokens + memory.approximate_token_count > max_tokens:
                continue
            seen.add(memory.id)
            selected.append(self._memory_out(memory))
            used_tokens += memory.approximate_token_count
        return ContextMetadata(usedTokens=used_tokens, maxContextTokens=max_tokens, memories=selected)

    def query(self, request: QueryRequest) -> QueryResponse:
        context = self.retrieve_context(request)
        answer, insufficient = self.llm.answer_from_context(request.query, [memory.content for memory in context.memories])
        supporting = [] if insufficient else context.memories
        return QueryResponse(
            answer=answer,
            insufficientContext=insufficient,
            context=context,
            supportingMemories=supporting,
        )

    def reset_demo(self) -> ResetDemoResponse:
        from backend.app.seed_data import seed_demo

        self.repository.reset_workspace("demo")
        return seed_demo(self)

    def _extract_with_retry(self, content: str):
        last_error: ValueError | None = None
        for _attempt in range(2):
            try:
                extracted = self.llm.extract_memories(content)
                for item in extracted:
                    if not item.content.strip():
                        raise ValueError("LLM returned an empty memory.")
                    if item.confidence < 0 or item.confidence > 1:
                        raise ValueError("LLM returned confidence outside 0..1.")
                    if not item.suggested_topic_name.strip():
                        raise ValueError("LLM returned a memory without a topic.")
                return extracted
            except ValueError as exc:
                last_error = exc
        raise ValueError(f"Memory extraction failed: {last_error}")

    def _assign_topic(self, workspace_id: str, memory) -> tuple[Topic, bool]:
        topics = self.repository.list_topics(workspace_id)
        candidates = [
            TopicCandidate(id=topic.id, name=topic.name, description=topic.description, galaxy_name=topic.galaxy_name)
            for topic in topics
        ]
        topic_id = self.llm.choose_topic(memory, candidates)
        if topic_id:
            existing = self.repository.find_topic_by_id(workspace_id, topic_id)
            if existing is not None:
                return existing, False

        galaxy = self.repository.get_or_create_galaxy(
            workspace_id,
            memory.suggested_galaxy_name,
            memory.suggested_galaxy_description,
        )
        topic = self.repository.create_topic(
            Topic(
                id=new_id(),
                workspace_id=workspace_id,
                galaxy_id=galaxy.id,
                galaxy_name=galaxy.name,
                name=memory.suggested_topic_name,
                description=memory.suggested_topic_description,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
        )
        return topic, topic.memory_count == 0

    def _ingest_response(
        self,
        message_id: str,
        status: str,
        duplicate: bool,
        memories: list[Memory],
        topics_created: int,
        topics_reused: int,
    ) -> MessageIngestResponse:
        return MessageIngestResponse(
            messageId=message_id,
            status=status,
            duplicate=duplicate,
            memoriesCreated=0 if duplicate else len(memories),
            topicsCreated=topics_created,
            topicsReused=topics_reused,
            memories=[
                IngestedMemory(
                    id=memory.id,
                    topicId=memory.topic_id,
                    topicName=memory.topic_name,
                    content=memory.content,
                    memoryType=memory.memory_type,
                    confidence=memory.confidence,
                )
                for memory in memories
            ],
        )

    def _topic_out(self, topic: Topic) -> TopicOut:
        return TopicOut(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            galaxy=GalaxyOut(id=topic.galaxy_id, name=topic.galaxy_name),
            memoryCount=topic.memory_count,
        )

    def _memory_out(self, memory: Memory) -> MemoryOut:
        return MemoryOut(
            id=memory.id,
            topicId=memory.topic_id,
            topicName=memory.topic_name,
            content=memory.content,
            memoryType=memory.memory_type,
            confidence=memory.confidence,
            createdAt=memory.created_at,
            source=MemorySource(
                messageId=memory.message_id,
                source=memory.source,
                sourceUrl=memory.source_url,
                timestamp=memory.source_timestamp,
            ),
            approximateTokenCount=memory.approximate_token_count,
        )
