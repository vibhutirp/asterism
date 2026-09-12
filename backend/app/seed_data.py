from __future__ import annotations

from backend.app.models import MessageIngestRequest, ResetDemoResponse


DEMO_MESSAGES = [
    {
        "conversationId": "seed-product",
        "externalId": "seed-atlas-onboarding-1",
        "content": "For Atlas, remove phone number from signup. Another Atlas onboarding idea: let people explore before signup.",
        "source": "seed",
    },
    {
        "conversationId": "seed-product",
        "externalId": "seed-atlas-pricing-1",
        "content": "For Atlas pricing, we should test annual pricing and a team plan.",
        "source": "seed",
    },
    {
        "conversationId": "seed-product",
        "externalId": "seed-launch-1",
        "content": "Launch planning should include beta customer quotes and a concise announcement.",
        "source": "seed",
    },
    {
        "conversationId": "seed-personal",
        "externalId": "seed-camping-1",
        "content": "I want to plan a camping trip and need to pack a stove, lantern, and warm layers.",
        "source": "seed",
    },
]


def seed_demo(engine) -> ResetDemoResponse:
    memories_created = 0
    for item in DEMO_MESSAGES:
        response = engine.ingest_message(
            MessageIngestRequest(
                workspaceId="demo",
                conversationId=item["conversationId"],
                externalId=item["externalId"],
                role="user",
                content=item["content"],
                source=item["source"],
                sourceUrl=None,
            )
        )
        memories_created += len(response.memories)
    topics_created = len(engine.list_topics("demo").topics)
    return ResetDemoResponse(workspaceId="demo", topicsCreated=topics_created, memoriesCreated=memories_created)
