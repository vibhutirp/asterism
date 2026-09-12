from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.dependencies import get_memory_engine
from backend.app.llm import HeuristicLLMClient
from backend.app.main import app
from backend.app.repository import PostgresMemoryRepository
from backend.app.service import MemoryEngine


def test_api_flow_persists_through_postgres(postgres_ready: str) -> None:
    workspace_id = f"api-{uuid4()}"
    repository = PostgresMemoryRepository(postgres_ready)
    engine = MemoryEngine(repository, HeuristicLLMClient(), default_context_tokens=get_settings().default_context_tokens)
    app.dependency_overrides[get_memory_engine] = lambda: engine
    client = TestClient(app)

    try:
        health = client.get("/api/health")
        ingest = client.post(
            "/api/messages",
            json={
                "workspaceId": workspace_id,
                "conversationId": "c1",
                "externalId": "e1",
                "role": "user",
                "content": "For Atlas pricing, we should test quarterly billing. Separately I want to plan a camping trip.",
                "source": "web",
                "sourceUrl": "https://example.test/e1",
            },
        )
        duplicate = client.post(
            "/api/messages",
            json={
                "workspaceId": workspace_id,
                "conversationId": "c1",
                "externalId": "e1",
                "role": "user",
                "content": "Changed content should be ignored as duplicate.",
                "source": "web",
                "sourceUrl": None,
            },
        )
        topics = client.get("/api/topics", params={"workspaceId": workspace_id})
        topic_id = topics.json()["topics"][0]["id"]
        detail = client.get(f"/api/topics/{topic_id}", params={"workspaceId": workspace_id})
        supported = client.post(
            "/api/query",
            json={
                "workspaceId": workspace_id,
                "query": "Atlas pricing quarterly",
                "maxContextTokens": 2000,
                "topicIds": [],
            },
        )
        unsupported = client.post(
            "/api/query",
            json={
                "workspaceId": workspace_id,
                "query": "payroll taxes",
                "maxContextTokens": 2000,
                "topicIds": [],
            },
        )
    finally:
        app.dependency_overrides.clear()
        repository.reset_workspace(workspace_id)

    assert health.status_code == 200
    assert ingest.status_code == 200
    assert ingest.json()["memoriesCreated"] == 2
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["memoriesCreated"] == 0
    assert topics.status_code == 200
    assert len(topics.json()["topics"]) == 2
    assert detail.status_code == 200
    assert detail.json()["memories"][0]["source"]["sourceUrl"] == "https://example.test/e1"
    assert supported.status_code == 200
    assert supported.json()["insufficientContext"] is False
    assert unsupported.status_code == 200
    assert unsupported.json()["insufficientContext"] is True
