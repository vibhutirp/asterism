from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.dependencies import get_memory_engine
from backend.app.in_memory_repository import InMemoryMemoryRepository
from backend.app.llm import HeuristicLLMClient
from backend.app.main import app
from backend.app.service import MemoryEngine


def make_client(engine: MemoryEngine) -> TestClient:
    app.dependency_overrides[get_memory_engine] = lambda: engine
    return TestClient(app)


def test_health_route_and_validation_error_shape() -> None:
    client = TestClient(app)

    health = client.get("/api/health")
    invalid = client.post(
        "/api/messages",
        json={
            "workspaceId": "demo",
            "conversationId": "c1",
            "externalId": "e1",
            "role": "user",
            "content": "",
            "source": "web",
            "sourceUrl": None,
        },
    )

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"


def test_ingest_value_error_is_bad_request() -> None:
    class FailingEngine:
        def ingest_message(self, _payload):
            raise ValueError("Memory extraction failed.")

    app.dependency_overrides[get_memory_engine] = lambda: FailingEngine()
    client = TestClient(app)

    try:
        response = client.post(
            "/api/messages",
            json={
                "workspaceId": "demo",
                "conversationId": "c1",
                "externalId": "e1",
                "role": "user",
                "content": "hello",
                "source": "web",
                "sourceUrl": None,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "bad_request", "message": "Memory extraction failed."}
    }


def test_topic_404_query_bounds_and_reset_route() -> None:
    engine = MemoryEngine(InMemoryMemoryRepository(), HeuristicLLMClient())
    client = make_client(engine)

    try:
        missing = client.get("/api/topics/not-found", params={"workspaceId": "demo"})
        invalid_query = client.post(
            "/api/query",
            json={"workspaceId": "demo", "query": "Atlas", "maxContextTokens": 0, "topicIds": []},
        )
        reset = client.post("/api/reset-demo")
    finally:
        app.dependency_overrides.clear()

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"
    assert invalid_query.status_code == 422
    assert invalid_query.json()["error"]["code"] == "validation_error"
    assert reset.status_code == 200
    assert reset.json()["workspaceId"] == "demo"
    assert reset.json()["topicsCreated"] >= 4
