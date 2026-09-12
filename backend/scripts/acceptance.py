"""PRD acceptance tests against the real OpenRouter-backed API.

Runs the full pipeline (ingestion -> extraction -> topic assignment -> retrieval
-> grounded answers) against a live server using the real OpenRouterLLMClient,
so it requires OPENROUTER_API_KEY (environment or .env) and a reachable
Postgres. Refuses to run without the key.

Usage (from the repo root):

    python -m backend.scripts.acceptance                 # starts its own server
    python -m backend.scripts.acceptance --base-url http://127.0.0.1:8000/api

Each run uses a fresh acceptance-<id> workspace, prints PASS/FAIL per test plus
the extracted topics/memories for the messy-transcript test, and exits non-zero
on any failure. Test numbers follow the PRD acceptance list.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from backend.app.config import get_settings

ROOT = Path(__file__).resolve().parents[2]
HTTP_TIMEOUT = 120


class Failure(Exception):
    """An acceptance expectation was not met."""


class Skip(Exception):
    """The test cannot run in this configuration."""


def expect(condition: object, message: str) -> None:
    if not condition:
        raise Failure(message)


def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class ManagedServer:
    def __init__(self, port: int):
        self.port = port
        self.process: subprocess.Popen[str] | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/api"

    def start(self) -> None:
        env = {**os.environ, "PYTHONPATH": str(ROOT)}
        self.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.monotonic() + 30
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                output = self.process.stdout.read() if self.process.stdout else ""
                raise RuntimeError(f"Server exited during startup:\n{output}")
            try:
                with urllib.request.urlopen(f"{self.base_url}/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, OSError) as exc:
                last_error = exc
            time.sleep(0.2)
        raise RuntimeError(f"Timed out waiting for server health: {last_error}")

    def stop(self) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)
        self.process = None

    def restart(self) -> None:
        self.stop()
        self.start()


def api_get(base_url: str, path: str) -> dict:
    with urllib.request.urlopen(base_url + path, timeout=HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode())


def api_post(base_url: str, path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode())


@dataclass
class Context:
    base_url: str
    server: ManagedServer | None
    workspace: str
    ingests: dict[str, dict] = field(default_factory=dict)
    invoice_topic_id: str | None = None


def ingest(ctx: Context, conversation_id: str, external_id: str, content: str) -> dict:
    return api_post(
        ctx.base_url,
        "/messages",
        {
            "workspaceId": ctx.workspace,
            "conversationId": conversation_id,
            "externalId": external_id,
            "role": "user",
            "content": content,
            "source": "acceptance",
            "sourceUrl": None,
        },
    )


def run_query(ctx: Context, question: str, max_context_tokens: int = 2000) -> dict:
    return api_post(
        ctx.base_url,
        "/query",
        {
            "workspaceId": ctx.workspace,
            "query": question,
            "maxContextTokens": max_context_tokens,
            "topicIds": [],
        },
    )


def topic_map(ctx: Context) -> dict[str, dict]:
    topics = api_get(ctx.base_url, f"/topics?workspaceId={ctx.workspace}")["topics"]
    return {topic["id"]: topic for topic in topics}


TEST_1_CONTENT = (
    "Three things on my mind: we should redesign the invoice PDF layout for Bloom clients. "
    "I want to start running twice a week before the marathon in May. "
    "And I need to renew my passport before the Lisbon trip."
)


def test_1_multi_concept_message(ctx: Context) -> str:
    response = ingest(ctx, "acc-conv-1", "acc-msg-1", TEST_1_CONTENT)
    ctx.ingests["msg1"] = response
    memories = response["memories"]
    topic_ids = {memory["topicId"] for memory in memories}
    expect(len(memories) >= 3, f"expected >=3 memories, got {len(memories)}")
    expect(len(topic_ids) >= 2, f"expected >=2 distinct topics, got {len(topic_ids)}")
    invoice_memories = [
        memory for memory in memories if "invoice" in memory["content"].lower() or "bloom" in memory["content"].lower()
    ]
    expect(invoice_memories, "no extracted memory mentions the Bloom invoice work")
    ctx.invoice_topic_id = invoice_memories[0]["topicId"]
    return f"{len(memories)} memories across {len(topic_ids)} topics"


def test_2_related_follow_up_grows_topic(ctx: Context) -> str:
    expect(ctx.invoice_topic_id, "invoice topic was not identified in Test 1")
    before = topic_map(ctx)
    before_count = before[ctx.invoice_topic_id]["memoryCount"]
    response = ingest(
        ctx,
        "acc-conv-1",
        "acc-msg-2",
        "Another thought on the Bloom invoice redesign: the totals section should show tax per line item.",
    )
    memories = response["memories"]
    expect(memories, "no memories extracted from the follow-up")
    stray = {memory["topicId"] for memory in memories} - {ctx.invoice_topic_id}
    expect(not stray, f"follow-up memories landed outside the existing invoice topic: {stray}")
    after = topic_map(ctx)
    expect(
        len(after) == len(before),
        f"a near-duplicate topic was created (topic count {len(before)} -> {len(after)})",
    )
    after_count = after[ctx.invoice_topic_id]["memoryCount"]
    expect(after_count > before_count, f"invoice topic memoryCount did not grow ({before_count} -> {after_count})")
    return f"invoice topic memoryCount {before_count} -> {after_count}, no new topics"


def test_3_related_memory_from_other_conversation(ctx: Context) -> str:
    expect(ctx.invoice_topic_id, "invoice topic was not identified in Test 1")
    response = ingest(
        ctx,
        "acc-conv-2",
        "acc-msg-3",
        "For the Bloom invoices, we should also add a due-date reminder line at the bottom.",
    )
    memories = response["memories"]
    expect(memories, "no memories extracted")
    stray = {memory["topicId"] for memory in memories} - {ctx.invoice_topic_id}
    expect(not stray, f"cross-conversation memory landed outside the invoice topic: {stray}")
    return "cross-conversation memory joined the same invoice topic"


def test_4_duplicate_external_id_is_idempotent(ctx: Context) -> str:
    before = topic_map(ctx)
    response = ingest(ctx, "acc-conv-1", "acc-msg-1", TEST_1_CONTENT)
    expect(response["duplicate"] is True, f"expected duplicate:true, got {response['duplicate']}")
    expect(response["memoriesCreated"] == 0, f"expected 0 new memories, got {response['memoriesCreated']}")
    expect(response["topicsCreated"] == 0, f"expected 0 new topics, got {response['topicsCreated']}")
    after = topic_map(ctx)
    expect(len(after) == len(before), "topic count changed on duplicate ingest")
    return "duplicate:true, nothing new created"


def test_5_topic_detail_has_provenance(ctx: Context) -> str:
    expect(ctx.invoice_topic_id, "invoice topic was not identified in Test 1")
    detail = api_get(ctx.base_url, f"/topics/{ctx.invoice_topic_id}?workspaceId={ctx.workspace}")
    memories = detail["memories"]
    expect(memories, "topic detail returned no memories")
    for memory in memories:
        source = memory.get("source") or {}
        expect(source.get("messageId"), f"memory {memory['id']} is missing source.messageId")
        expect(source.get("timestamp"), f"memory {memory['id']} is missing source.timestamp")
    return f"all {len(memories)} memories carry source messageId + timestamp"


def test_7_grounded_multi_memory_answer(ctx: Context) -> str:
    response = run_query(ctx, "What changes are we planning for the Bloom invoice redesign?")
    expect(response["insufficientContext"] is False, "query unexpectedly reported insufficient context")
    expect(response["answer"].strip(), "query returned an empty answer")
    expect(response["supportingMemories"], "no supportingMemories returned")
    return f"answer grounded in {len(response['supportingMemories'])} supporting memories"


def test_8_unknown_subject_reports_insufficient_context(ctx: Context) -> str:
    response = run_query(ctx, "What did we decide about the office lease renewal?")
    expect(response["insufficientContext"] is True, f"expected insufficientContext:true, got answer: {response['answer']!r}")
    expect(response["supportingMemories"] == [], "supportingMemories should be empty when context is insufficient")
    return "insufficientContext:true with no supporting memories"


def test_9_data_survives_server_restart(ctx: Context) -> str:
    if ctx.server is None:
        raise Skip("targeting an externally managed server; cannot restart it")
    before = {(topic_id, topic["memoryCount"]) for topic_id, topic in topic_map(ctx).items()}
    expect(before, "no topics existed before restart")
    ctx.server.restart()
    after = {(topic_id, topic["memoryCount"]) for topic_id, topic in topic_map(ctx).items()}
    expect(after == before, f"topics changed across restart: before={sorted(before)} after={sorted(after)}")
    return f"{len(before)} topics with identical memory counts after restart"


def test_10_topics_endpoint_returns_stored_data(ctx: Context) -> str:
    topics = topic_map(ctx)
    expect(topics, "GET /api/topics returned no topics")
    expect(ctx.invoice_topic_id in topics, "invoice topic missing from GET /api/topics")
    invoice_count = topics[ctx.invoice_topic_id]["memoryCount"]
    expect(invoice_count >= 3, f"invoice topic should hold >=3 memories, has {invoice_count}")
    return f"{len(topics)} topics returned; invoice topic holds {invoice_count} memories"


def test_11_context_budget_is_bounded(ctx: Context) -> str:
    response = run_query(ctx, "What changes are we planning for the Bloom invoice redesign?", max_context_tokens=50)
    context = response["context"]
    expect(context["maxContextTokens"] == 50, f"maxContextTokens echoed as {context['maxContextTokens']}")
    expect(
        context["usedTokens"] <= 50,
        f"usedTokens {context['usedTokens']} exceeds the 50-token budget",
    )
    return f"usedTokens {context['usedTokens']} <= 50"


MESSY_TRANSCRIPT = [
    (
        "acc-messy-1",
        "I'm debating whether to sign up for the hackathon in two weekends. It's 24 hours and I'd have to "
        "find a team, but the theme is AI agents which is right up my alley.",
    ),
    (
        "acc-messy-2",
        "If I do it, I should probably finally replace my laptop — this one thermal-throttles the moment I "
        "open Docker. Thinking either a MacBook Air M3 or a ThinkPad X1 Carbon.",
    ),
    (
        "acc-messy-3",
        "Also need to order groceries this week and I keep forgetting to buy a birthday gift for my sister, "
        "maybe those ceramic mugs she liked.",
    ),
    (
        "acc-messy-4",
        "Decided: I'm doing the hackathon. Registered tonight.",
    ),
]

LAPTOP_KEYWORDS = ("laptop", "macbook", "thinkpad")


def classify(content: str) -> str | None:
    lowered = content.lower()
    if any(keyword in lowered for keyword in LAPTOP_KEYWORDS):
        return "laptop"
    if "hackathon" in lowered:
        return "hackathon"
    return None


def test_12_messy_transcript_structure(ctx: Context) -> str:
    responses: dict[str, dict] = {}
    for external_id, content in MESSY_TRANSCRIPT:
        responses[external_id] = ingest(ctx, "acc-conv-messy", external_id, content)

    all_memories = [
        (external_id, memory) for external_id, response in responses.items() for memory in response["memories"]
    ]
    expect(all_memories, "no memories extracted from the transcript")

    print("\n  --- Test 12: extracted topics and memories ---")
    by_topic: dict[str, list[tuple[str, dict]]] = {}
    for external_id, memory in all_memories:
        by_topic.setdefault(memory["topicId"], []).append((external_id, memory))
    for topic_id, entries in by_topic.items():
        print(f"  Topic: {entries[0][1]['topicName']!r} ({topic_id})")
        for external_id, memory in entries:
            print(f"    [{memory['memoryType']:>10}] ({external_id}) {memory['content']}")
    print("  --- end Test 12 output ---\n")

    topic_ids = set(by_topic)
    expect(len(topic_ids) >= 3, f"expected >=3 distinct topics, got {len(topic_ids)}")

    decision_types = [memory["memoryType"] for memory in responses["acc-messy-4"]["memories"]]
    expect("decision" in decision_types, f"msg-4 should yield a decision memory, got types {decision_types}")
    msg1_types = [memory["memoryType"] for memory in responses["acc-messy-1"]["memories"]]
    expect(
        "decision" not in msg1_types,
        f"msg-1 is deliberation, not a decision, but got types {msg1_types}",
    )

    hackathon_topics = {memory["topicId"] for _, memory in all_memories if classify(memory["content"]) == "hackathon"}
    laptop_topics = {memory["topicId"] for _, memory in all_memories if classify(memory["content"]) == "laptop"}
    expect(hackathon_topics, "no hackathon-related memories found")
    expect(laptop_topics, "no laptop-related memories found")
    expect(
        not (hackathon_topics & laptop_topics),
        f"a topic contains both hackathon and laptop memories: {hackathon_topics & laptop_topics}",
    )
    expect(
        len(hackathon_topics) == 1,
        f"hackathon memories are split across {len(hackathon_topics)} topics: {hackathon_topics}",
    )
    return (
        f"{len(all_memories)} memories across {len(topic_ids)} topics; decision captured; "
        "hackathon and laptop topics separate"
    )


TESTS = [
    ("Test 1: one message with three unrelated concepts", test_1_multi_concept_message),
    ("Test 2: related follow-up grows the existing topic", test_2_related_follow_up_grows_topic),
    ("Test 3: related memory from a different conversation", test_3_related_memory_from_other_conversation),
    ("Test 4: duplicate externalId is idempotent", test_4_duplicate_external_id_is_idempotent),
    ("Test 5: topic detail carries provenance", test_5_topic_detail_has_provenance),
    ("Test 7: grounded answer with supporting memories", test_7_grounded_multi_memory_answer),
    ("Test 8: unknown subject yields insufficientContext", test_8_unknown_subject_reports_insufficient_context),
    ("Test 9: topics and memories survive server restart", test_9_data_survives_server_restart),
    ("Test 10: GET /api/topics returns stored data", test_10_topics_endpoint_returns_stored_data),
    ("Test 11: maxContextTokens=50 bounds the context", test_11_context_budget_is_bounded),
    ("Test 12: messy transcript lands in sensible structure", test_12_messy_transcript_structure),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PRD acceptance tests against the live LLM-backed API.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Target an already-running server (e.g. http://127.0.0.1:8000/api) instead of starting one.",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.openrouter_api_key:
        print("Refusing to run: OPENROUTER_API_KEY is not set (environment or .env).", file=sys.stderr)
        print("These acceptance tests are only meaningful against the real OpenRouterLLMClient.", file=sys.stderr)
        raise SystemExit(2)

    server: ManagedServer | None = None
    if args.base_url:
        base_url = args.base_url.rstrip("/")
    else:
        server = ManagedServer(free_port())
        server.start()
        base_url = server.base_url

    workspace = f"acceptance-{uuid4().hex[:8]}"
    ctx = Context(base_url=base_url, server=server, workspace=workspace)
    print(f"Acceptance run against {base_url} | workspace={workspace} | model={settings.openrouter_model}\n")

    failures = 0
    try:
        for name, test in TESTS:
            try:
                detail = test(ctx)
                print(f"PASS  {name}" + (f" — {detail}" if detail else ""))
            except Skip as exc:
                print(f"SKIP  {name} — {exc}")
            except Failure as exc:
                failures += 1
                print(f"FAIL  {name} — {exc}")
            except Exception as exc:  # noqa: BLE001 - report and keep going
                failures += 1
                print(f"FAIL  {name} — unexpected error: {exc!r}")
    finally:
        if server is not None:
            server.stop()

    print(f"\n{len(TESTS) - failures}/{len(TESTS)} passed; workspace {workspace!r} left in the database for inspection.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
