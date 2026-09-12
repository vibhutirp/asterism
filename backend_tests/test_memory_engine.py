from fastapi.testclient import TestClient

from backend.app.dependencies import get_memory_engine
from backend.app.in_memory_repository import InMemoryMemoryRepository
from backend.app.llm import HeuristicLLMClient
from backend.app.main import app
from backend.app.models import MessageIngestRequest, QueryRequest
from backend.app.service import MemoryEngine


def make_engine() -> MemoryEngine:
    return MemoryEngine(InMemoryMemoryRepository(), HeuristicLLMClient())


def test_one_message_creates_multiple_topics() -> None:
    engine = make_engine()
    response = engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="For Atlas, remove phone number from signup. Separately I want to plan a camping trip.",
            source="web",
            sourceUrl=None,
        )
    )

    topic_names = {memory.topic_name for memory in response.memories}
    assert response.memories_created == 2
    assert "Atlas Onboarding" in topic_names
    assert "Camping Trip" in topic_names


def test_related_follow_up_reuses_topic() -> None:
    engine = make_engine()
    first = engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="For Atlas, remove phone number from signup.",
            source="web",
            sourceUrl=None,
        )
    )
    second = engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e2",
            role="user",
            content="Another Atlas onboarding idea: let people explore before signup.",
            source="web",
            sourceUrl=None,
        )
    )

    assert first.memories[0].topic_id == second.memories[0].topic_id
    assert second.topics_reused == 1


def test_duplicate_external_event_is_idempotent() -> None:
    engine = make_engine()
    payload = MessageIngestRequest(
        workspaceId="demo",
        conversationId="c1",
        externalId="e1",
        role="user",
        content="For Atlas pricing, we should test annual pricing.",
        source="web",
        sourceUrl=None,
    )

    first = engine.ingest_message(payload)
    second = engine.ingest_message(payload)

    assert second.duplicate is True
    assert second.message_id == first.message_id
    assert len(second.memories) == len(first.memories)
    assert len(engine.list_topics("demo").topics) == 1


def test_provenance_and_topic_detail_are_preserved() -> None:
    engine = make_engine()
    response = engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="Launch planning should include beta customer quotes.",
            source="slack",
            sourceUrl="https://example.test/msg",
        )
    )

    detail = engine.get_topic("demo", response.memories[0].topic_id)

    assert detail is not None
    assert detail.memories[0].source.message_id == response.message_id
    assert detail.memories[0].source.source == "slack"
    assert detail.memories[0].source.source_url == "https://example.test/msg"


def test_retrieval_and_insufficient_context() -> None:
    engine = make_engine()
    engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="For Atlas, remove phone number from signup.",
            source="web",
            sourceUrl=None,
        )
    )

    supported = engine.query(
        QueryRequest(workspaceId="demo", query="What signup changes for Atlas?", maxContextTokens=2000, topicIds=[])
    )
    unsupported = engine.query(
        QueryRequest(workspaceId="demo", query="What did we decide about payroll?", maxContextTokens=2000, topicIds=[])
    )

    assert supported.insufficient_context is False
    assert supported.supporting_memories
    assert unsupported.insufficient_context is True


def test_context_budget_is_respected() -> None:
    engine = make_engine()
    engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="For Atlas, remove phone number from signup.",
            source="web",
            sourceUrl=None,
        )
    )

    context = engine.retrieve_context(
        QueryRequest(workspaceId="demo", query="Atlas signup phone", maxContextTokens=3, topicIds=[])
    )

    assert context.used_tokens <= 3


def test_data_persists_across_service_restart_with_same_repository() -> None:
    repository = InMemoryMemoryRepository()
    first_engine = MemoryEngine(repository, HeuristicLLMClient())
    first_engine.ingest_message(
        MessageIngestRequest(
            workspaceId="demo",
            conversationId="c1",
            externalId="e1",
            role="user",
            content="For Atlas pricing, we should test annual pricing.",
            source="web",
            sourceUrl=None,
        )
    )

    restarted_engine = MemoryEngine(repository, HeuristicLLMClient())

    assert restarted_engine.list_topics("demo").topics[0].name == "Atlas Pricing"


def test_reset_demo_seeds_expected_topics() -> None:
    engine = make_engine()
    response = engine.reset_demo()
    topic_names = {topic.name for topic in engine.list_topics("demo").topics}

    assert response.workspace_id == "demo"
    assert response.memories_created >= 4
    assert {"Atlas Onboarding", "Atlas Pricing", "Launch", "Camping Trip"} <= topic_names


def test_api_request_response_shapes_work() -> None:
    engine = make_engine()
    app.dependency_overrides[get_memory_engine] = lambda: engine
    client = TestClient(app)

    try:
        ingest = client.post(
            "/api/messages",
            json={
                "workspaceId": "demo",
                "conversationId": "c1",
                "externalId": "e1",
                "role": "user",
                "content": "For Atlas, remove phone number from signup.",
                "source": "web",
                "sourceUrl": None,
            },
        )
        topics = client.get("/api/topics", params={"workspaceId": "demo"})
        query = client.post(
            "/api/query",
            json={"workspaceId": "demo", "query": "Atlas signup", "maxContextTokens": 2000, "topicIds": []},
        )
    finally:
        app.dependency_overrides.clear()

    assert ingest.status_code == 200
    assert ingest.json()["memoriesCreated"] == 1
    assert topics.status_code == 200
    assert topics.json()["topics"][0]["memoryCount"] == 1
    assert query.status_code == 200
    assert query.json()["insufficientContext"] is False
