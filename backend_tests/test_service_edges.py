from __future__ import annotations

import pytest

from backend.app.domain import ExtractedMemory
from backend.app.in_memory_repository import InMemoryMemoryRepository
from backend.app.llm import HeuristicLLMClient, LLMClient
from backend.app.models import MemoryType, MessageIngestRequest, QueryRequest
from backend.app.service import MemoryEngine


def request(content: str = "For Atlas, remove phone number from signup.") -> MessageIngestRequest:
    return MessageIngestRequest(
        workspaceId="demo",
        conversationId="c1",
        externalId="e1",
        role="user",
        content=content,
        source="web",
        sourceUrl=None,
    )


class EmptyLLM(HeuristicLLMClient):
    def extract_memories(self, _message: str) -> list[ExtractedMemory]:
        return []


class BadConfidenceLLM(HeuristicLLMClient):
    def extract_memories(self, _message: str) -> list[ExtractedMemory]:
        return [
            ExtractedMemory(
                content="Invalid confidence.",
                memory_type=MemoryType.idea,
                confidence=1.2,
                suggested_topic_name="Invalid",
                suggested_topic_description="Invalid",
                suggested_galaxy_name="Invalid",
                suggested_galaxy_description="Invalid",
            )
        ]


class EmptyContentLLM(HeuristicLLMClient):
    def extract_memories(self, _message: str) -> list[ExtractedMemory]:
        return [
            ExtractedMemory(
                content="",
                memory_type=MemoryType.idea,
                confidence=0.7,
                suggested_topic_name="Invalid",
                suggested_topic_description="Invalid",
                suggested_galaxy_name="Invalid",
                suggested_galaxy_description="Invalid",
            )
        ]


class EmptyTopicLLM(HeuristicLLMClient):
    def extract_memories(self, _message: str) -> list[ExtractedMemory]:
        return [
            ExtractedMemory(
                content="Valid content.",
                memory_type=MemoryType.idea,
                confidence=0.7,
                suggested_topic_name="",
                suggested_topic_description="Invalid",
                suggested_galaxy_name="Invalid",
                suggested_galaxy_description="Invalid",
            )
        ]


def test_empty_extraction_marks_message_processed_with_no_memories() -> None:
    repository = InMemoryMemoryRepository()
    engine = MemoryEngine(repository, EmptyLLM())

    response = engine.ingest_message(request())
    stored = repository.find_message("demo", "web", "e1")

    assert response.status == "processed"
    assert response.memories_created == 0
    assert response.memories == []
    assert stored.processing_status == "processed"


@pytest.mark.parametrize("llm", [BadConfidenceLLM(), EmptyContentLLM(), EmptyTopicLLM()])
def test_invalid_extraction_is_retried_then_marks_message_failed(llm: LLMClient) -> None:
    repository = InMemoryMemoryRepository()
    engine = MemoryEngine(repository, llm)

    with pytest.raises(ValueError, match="Memory extraction failed"):
        engine.ingest_message(request())

    stored = repository.find_message("demo", "web", "e1")
    assert stored.processing_status == "failed"


def test_topic_id_filter_excludes_unrelated_memories() -> None:
    engine = MemoryEngine(InMemoryMemoryRepository(), HeuristicLLMClient())
    onboarding = engine.ingest_message(request("For Atlas, remove phone number from signup."))
    pricing = engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e2",
            role="user",
            content="For Atlas pricing, we should test annual pricing.",
            source="web",
            sourceUrl=None,
        )
    )

    context = engine.retrieve_context(
        QueryRequest(
            workspaceId="demo",
            query="pricing annual",
            maxContextTokens=2000,
            topicIds=[onboarding.memories[0].topic_id],
        )
    )

    assert pricing.memories[0].topic_id != onboarding.memories[0].topic_id
    assert context.memories == []


def test_heuristic_memory_type_classification_edges() -> None:
    llm = HeuristicLLMClient()

    cases = {
        "Will ship Atlas signup.": MemoryType.decision,
        "What should we do about Atlas pricing?": MemoryType.question,
        "I prefer annual billing.": MemoryType.preference,
        "Need to plan launch.": MemoryType.task,
    }

    for text, expected in cases.items():
        assert llm.extract_memories(text)[0].memory_type == expected


def test_preference_with_word_plan_is_currently_classified_as_task() -> None:
    llm = HeuristicLLMClient()

    memory = llm.extract_memories("I prefer annual plan.")[0]

    assert memory.memory_type == MemoryType.task
