"""Slack Socket Mode adapter (DM-only).

Zero business logic lives here: DM events are normalized into
MessageIngestRequest and handed to MemoryEngine.ingest_message; "ask:" messages
are routed to MemoryEngine.query. Slack retry deliveries are absorbed by the
engine's (workspace, source, externalId) idempotency, and Bolt acknowledges
event envelopes automatically before our (slow, LLM-bound) handler work runs.
"""
from __future__ import annotations

from backend.app.models import MessageIngestRequest, QueryRequest
from backend.app.service import MemoryEngine

ASK_PREFIX = "ask:"
WORKSPACE_ID = "demo"


def normalize_dm_event(
    event: dict,
    event_id: str | None = None,
    permalink: str | None = None,
    workspace_id: str = WORKSPACE_ID,
) -> MessageIngestRequest | None:
    """Map a Slack DM message event to an ingest request, or None to ignore it.

    Ignored: anything with a subtype (edits, deletions, joins, bot_message),
    bot-authored messages, and events without text/user/channel.
    """
    if event.get("type") != "message":
        return None
    if event.get("subtype"):
        return None
    if event.get("bot_id"):
        return None
    text = (event.get("text") or "").strip()
    if not text or not event.get("user") or not event.get("channel"):
        return None
    external_id = event_id or event.get("client_msg_id") or event.get("ts")
    if not external_id:
        return None
    return MessageIngestRequest(
        workspaceId=workspace_id,
        conversationId=event["channel"],
        externalId=external_id,
        role="user",
        content=text,
        source="slack",
        sourceUrl=permalink,
    )


def format_ingest_reply(response) -> str:
    if response.duplicate:
        return "I already have that message saved."
    if not response.memories:
        return "I did not find anything to remember in that message."
    names = sorted({memory.topic_name for memory in response.memories})
    return f"Organized that into {len(names)} topic(s): {', '.join(names)}"


def format_query_reply(response) -> str:
    count = len(response.supporting_memories)
    noun = "source memory" if count == 1 else "source memories"
    return f"{response.answer}\n({count} {noun})"


def create_slack_app(engine: MemoryEngine, bot_token: str):
    from slack_bolt import App

    app = App(token=bot_token)

    @app.event("message")
    def handle_dm(body, event, say, client) -> None:
        if event.get("channel_type") != "im":
            return
        request = normalize_dm_event(event, event_id=body.get("event_id"))
        if request is None:
            return

        if request.content.lower().startswith(ASK_PREFIX):
            question = request.content[len(ASK_PREFIX):].strip()
            if not question:
                say(f"Ask me something after '{ASK_PREFIX}'.")
                return
            say(format_query_reply(engine.query(QueryRequest(workspaceId=request.workspace_id, query=question))))
            return

        try:
            permalink = client.chat_getPermalink(channel=event["channel"], message_ts=event["ts"])["permalink"]
            request = request.model_copy(update={"source_url": permalink})
        except Exception:
            pass  # provenance still carries messageId/timestamp without a permalink
        say(format_ingest_reply(engine.ingest_message(request)))

    return app
