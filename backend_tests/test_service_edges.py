from __future__ import annotations

import pytest

from backend.app.domain import ExtractedMemory, Memory, Topic, new_id, utc_now
from backend.app.in_memory_repository import InMemoryMemoryRepository
from backend.app.llm import HeuristicLLMClient, LLMClient, TopicCandidate
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


def test_llm_base_client_methods_are_abstract() -> None:
    llm = LLMClient()

    with pytest.raises(NotImplementedError):
        llm.extract_memories("hello")
    with pytest.raises(NotImplementedError):
        llm.choose_topic(
            ExtractedMemory(
                content="hello",
                memory_type=MemoryType.idea,
                confidence=0.5,
                suggested_topic_name="General Notes",
                suggested_topic_description="General",
                suggested_galaxy_name="Personal",
                suggested_galaxy_description="Personal",
            ),
            [],
        )
    with pytest.raises(NotImplementedError):
        llm.answer_from_context("hello", [])


def test_heuristic_choose_topic_by_overlapping_terms_and_unsupported_context() -> None:
    llm = HeuristicLLMClient()
    memory = ExtractedMemory(
        content="Atlas onboarding should be lighter.",
        memory_type=MemoryType.idea,
        confidence=0.8,
        suggested_topic_name="Atlas Onboarding Ideas",
        suggested_topic_description="Signup work",
        suggested_galaxy_name="Product",
        suggested_galaxy_description="Product",
    )

    chosen = llm.choose_topic(
        memory,
        [
            TopicCandidate(id="pricing", name="Atlas Pricing", description="Pricing", galaxy_name="Product"),
            TopicCandidate(id="onboarding", name="Atlas Onboarding", description="Signup", galaxy_name="Product"),
        ],
    )
    answer, insufficient = llm.answer_from_context("payroll", ["For Atlas, remove phone number from signup."])

    assert chosen == "onboarding"
    assert insufficient is True
    assert answer == "I do not have enough stored context to answer that."


def test_retrieve_context_deduplicates_repository_results() -> None:
    class DuplicateSearchRepository(InMemoryMemoryRepository):
        def search_memories(self, workspace_id: str, query: str, topic_ids: list[str], limit: int) -> list[Memory]:
            results = super().search_memories(workspace_id, query, topic_ids, limit)
            return results + results

    engine = MemoryEngine(DuplicateSearchRepository(), HeuristicLLMClient())
    engine.ingest_message(request())

    context = engine.retrieve_context(
        QueryRequest(workspaceId="demo", query="Atlas signup", maxContextTokens=2000, topicIds=[])
    )

    assert len(context.memories) == 1


def test_in_memory_duplicate_topic_creation_returns_existing_topic() -> None:
    repository = InMemoryMemoryRepository()
    galaxy = repository.get_or_create_galaxy("demo", "Product", "Product notes")
    topic = Topic(
        id=new_id(),
        workspace_id="demo",
        galaxy_id=galaxy.id,
        galaxy_name=galaxy.name,
        name="Atlas Pricing",
        description="Pricing",
        created_at=utc_now(),
        updated_at=utc_now(),
    )

    first = repository.create_topic(topic)
    second = repository.create_topic(
        Topic(
            id=new_id(),
            workspace_id="demo",
            galaxy_id=galaxy.id,
            galaxy_name=galaxy.name,
            name="Atlas Pricing",
            description="Duplicate",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
    )

    assert second.id == first.id
