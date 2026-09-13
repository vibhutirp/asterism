from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import pytest

from backend.app.repository import PostgresMemoryRepository


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
        except PermissionError as exc:
            pytest.skip(f"Local server sockets are not permitted: {exc}")
        return int(sock.getsockname()[1])


def wait_for_url(url: str, process: subprocess.Popen[str], expected_status: int = 200) -> str:
    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            if "operation not permitted" in output.lower():
                pytest.skip(f"Local server sockets are not permitted: {output}")
            pytest.fail(f"Server exited before {url} became ready:\n{output}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                body = response.read().decode(errors="ignore")
                if response.status == expected_status:
                    return body
        except urllib.error.HTTPError as exc:
            if exc.code == expected_status:
                return exc.read().decode(errors="ignore")
            last_error = exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, PermissionError):
                pytest.skip(f"Local HTTP sockets are not permitted: {exc}")
            last_error = exc
        time.sleep(0.2)
    pytest.fail(f"Timed out waiting for {url}: {last_error}")


@pytest.fixture
def live_api(postgres_ready: str):
    port = free_port()
    env = {**os.environ, "DATABASE_URL": postgres_ready, "PYTHONPATH": str(ROOT)}
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wait_for_url(f"http://127.0.0.1:{port}/api/health", process)
    try:
        yield f"http://127.0.0.1:{port}/api"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def api_get(base_url: str, path: str):
    with urllib.request.urlopen(base_url + path, timeout=10) as response:
        return response.status, json.loads(response.read().decode())


def api_post(base_url: str, path: str, payload: dict):
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode())


def test_live_fastapi_http_e2e_flow(live_api: str, postgres_ready: str) -> None:
    workspace_id = f"live-{uuid4()}"
    repository = PostgresMemoryRepository(postgres_ready)

    try:
        status, health = api_get(live_api, "/health")
        docs = urllib.request.urlopen(live_api.removesuffix("/api") + "/docs", timeout=10)
        status_topics, initial_topics = api_get(live_api, f"/topics?workspaceId={workspace_id}")
        status_ingest, ingest = api_post(
            live_api,
            "/messages",
            {
                "workspaceId": workspace_id,
                "conversationId": "browser-e2e",
                "externalId": "event-1",
                "role": "user",
                "content": "For Atlas pricing, we should test quarterly billing. Separately I want to plan a camping trip.",
                "source": "live-e2e",
                "sourceUrl": "https://example.test/live",
            },
        )
        status_duplicate, duplicate = api_post(
            live_api,
            "/messages",
            {
                "workspaceId": workspace_id,
                "conversationId": "browser-e2e",
                "externalId": "event-1",
                "role": "user",
                "content": "Changed duplicate content.",
                "source": "live-e2e",
                "sourceUrl": None,
            },
        )
        status_after_topics, after_topics = api_get(live_api, f"/topics?workspaceId={workspace_id}")
        topic_id = after_topics["topics"][0]["id"]
        status_detail, detail = api_get(live_api, f"/topics/{topic_id}?workspaceId={workspace_id}")
        status_query, query = api_post(
            live_api,
            "/query",
            {
                "workspaceId": workspace_id,
                "query": "Atlas pricing quarterly",
                "maxContextTokens": 2000,
                "topicIds": [],
            },
        )
    finally:
        repository.reset_workspace(workspace_id)

    assert status == 200
    assert health == {"status": "ok"}
    assert docs.status == 200
    assert "swagger-ui" in docs.read().decode(errors="ignore").lower()
    assert status_topics == 200
    assert initial_topics == {"topics": []}
    assert status_ingest == 200
    assert ingest["memoriesCreated"] == 2
    assert status_duplicate == 200
    assert duplicate["duplicate"] is True
    assert duplicate["memoriesCreated"] == 0
    assert status_after_topics == 200
    assert len(after_topics["topics"]) == 2
    assert status_detail == 200
    assert detail["memories"][0]["source"]["sourceUrl"] == "https://example.test/live"
    assert status_query == 200
    assert query["insufficientContext"] is False
