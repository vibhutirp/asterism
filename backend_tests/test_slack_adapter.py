from __future__ import annotations

from datetime import datetime, timezone

from backend.app.models import (
    ContextMetadata,
    IngestedMemory,
    MemoryOut,
    MemorySource,
    MemoryType,
    MessageIngestResponse,
    QueryResponse,
)
from backend.app.slack_adapter import format_ingest_reply, format_query_reply, normalize_dm_event


def dm_event(**overrides) -> dict:
    event = {
        "type": "message",
        "channel": "D0123456789",
        "channel_type": "im",
        "user": "U0123456789",
        "text": "For Atlas, remove phone number from signup.",
        "ts": "1757600000.000100",
        "client_msg_id": "client-msg-1",
    }
    event.update(overrides)
    return event


def ingest_response(topic_names: list[str], duplicate: bool = False) -> MessageIngestResponse:
    return MessageIngestResponse(
        messageId="m-1",
        status="processed",
        duplicate=duplicate,
        memoriesCreated=0 if duplicate else len(topic_names),
        topicsCreated=0,
        topicsReused=0,
        memories=[
            IngestedMemory(
                id=f"mem-{index}",
                topicId=f"t-{index}",
                topicName=name,
                content="Some memory.",
                memoryType=MemoryType.idea,
                confidence=0.9,
            )
            for index, name in enumerate(topic_names)
        ],
    )


def memory_out(memory_id: str) -> MemoryOut:
    now = datetime.now(timezone.utc)
    return MemoryOut(
        id=memory_id,
        topicId="t-1",
        topicName="Atlas Onboarding",
        content="Remove phone number from signup.",
        memoryType=MemoryType.idea,
        confidence=0.9,
        createdAt=now,
        source=MemorySource(messageId="m-1", source="slack", sourceUrl=None, timestamp=now),
        approximateTokenCount=6,
    )


def query_response(memory_ids: list[str], answer: str = "Remove phone number from signup.") -> QueryResponse:
    memories = [memory_out(memory_id) for memory_id in memory_ids]
    return QueryResponse(
        answer=answer,
        insufficientContext=not memories,
        context=ContextMetadata(usedTokens=6 * len(memories), maxContextTokens=2000, memories=memories),
        supportingMemories=memories,
    )


def test_normalize_maps_dm_event_to_ingest_request() -> None:
    request = normalize_dm_event(dm_event(), event_id="Ev0123456789", permalink="https://slack.test/p1")

    assert request is not None
    assert request.workspace_id == "demo"
    assert request.conversation_id == "D0123456789"
    assert request.external_id == "Ev0123456789"
    assert request.role == "user"
    assert request.content == "For Atlas, remove phone number from signup."
    assert request.source == "slack"
    assert request.source_url == "https://slack.test/p1"


def test_normalize_external_id_falls_back_to_client_msg_id_then_ts() -> None:
    no_event_id = normalize_dm_event(dm_event())
    no_client_msg_id = normalize_dm_event(dm_event(client_msg_id=None))

    assert no_event_id.external_id == "client-msg-1"
    assert no_client_msg_id.external_id == "1757600000.000100"


def test_normalize_ignores_bot_and_self_messages() -> None:
    assert normalize_dm_event(dm_event(bot_id="B0123456789")) is None
    assert normalize_dm_event(dm_event(user=None)) is None


def test_normalize_ignores_edits_and_other_subtypes() -> None:
    assert normalize_dm_event(dm_event(subtype="message_changed")) is None
    assert normalize_dm_event(dm_event(subtype="message_deleted")) is None
    assert normalize_dm_event(dm_event(subtype="bot_message")) is None


def test_normalize_ignores_non_message_and_empty_events() -> None:
    assert normalize_dm_event(dm_event(type="reaction_added")) is None
    assert normalize_dm_event(dm_event(text="   ")) is None
    assert normalize_dm_event(dm_event(text=None)) is None
    assert normalize_dm_event(dm_event(channel=None)) is None
    assert normalize_dm_event(dm_event(client_msg_id=None, ts=None)) is None


def test_normalize_strips_whitespace_from_content() -> None:
    request = normalize_dm_event(dm_event(text="  hello world  "))

    assert request.content == "hello world"


def test_format_ingest_reply_lists_distinct_topic_names() -> None:
    reply = format_ingest_reply(ingest_response(["Camping Trip", "Atlas Onboarding", "Atlas Onboarding"]))

    assert reply == "Organized that into 2 topic(s): Atlas Onboarding, Camping Trip"


def test_format_ingest_reply_handles_duplicates_and_empty() -> None:
    assert format_ingest_reply(ingest_response(["Atlas Onboarding"], duplicate=True)) == "I already have that message saved."
    assert format_ingest_reply(ingest_response([])) == "I did not find anything to remember in that message."


def test_format_query_reply_counts_sources() -> None:
    one = format_query_reply(query_response(["mem-1"]))
    two = format_query_reply(query_response(["mem-1", "mem-2"]))

    assert one == "Remove phone number from signup.\n(1 source memory)"
    assert two == "Remove phone number from signup.\n(2 source memories)"
