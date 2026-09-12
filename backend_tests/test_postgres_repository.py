from __future__ import annotations

from uuid import uuid4

from backend.app.domain import Memory, Message, Topic, new_id, utc_now
from backend.app.models import MemoryType
from backend.app.repository import PostgresMemoryRepository


def test_postgres_repository_crud_search_and_reset(postgres_ready: str) -> None:
    repository = PostgresMemoryRepository(postgres_ready)
    workspace_id = f"repo-{uuid4()}"

    try:
        workspace = repository.ensure_workspace(workspace_id, "Repository Test")
        assert workspace.id == workspace_id
        assert repository.ensure_workspace(workspace_id, "Ignored Name").name == "Repository Test"

        conversation = repository.get_or_create_conversation(workspace_id, "external-c1", "web")
        same_conversation = repository.get_or_create_conversation(workspace_id, "external-c1", "web")
        assert same_conversation.id == conversation.id

        created_at = utc_now()
        message = repository.create_message(
            Message(
                id=new_id(),
                workspace_id=workspace_id,
                conversation_id=conversation.id,
                external_id="message-1",
                role="user",
                content="For Atlas pricing, test quarterly billing.",
                source="web",
                source_url="https://example.test/source",
                created_at=created_at,
                processed_at=None,
                processing_status="processing",
            )
        )
        assert repository.find_message(workspace_id, "web", "message-1").id == message.id

        repository.update_message_status(message.id, "processed")
        assert repository.find_message(workspace_id, "web", "message-1").processing_status == "processed"

        galaxy = repository.get_or_create_galaxy(workspace_id, "Product", "Product notes")
        same_galaxy = repository.get_or_create_galaxy(workspace_id, "Product", "Other description")
        assert same_galaxy.id == galaxy.id

        topic = repository.create_topic(
            Topic(
                id=new_id(),
                workspace_id=workspace_id,
                galaxy_id=galaxy.id,
                galaxy_name=galaxy.name,
                name="Atlas Pricing",
                description="Pricing experiments",
                created_at=utc_now(),
                updated_at=utc_now(),
            )
        )
        duplicate_topic = repository.create_topic(
            Topic(
                id=new_id(),
                workspace_id=workspace_id,
                galaxy_id=galaxy.id,
                galaxy_name=galaxy.name,
                name="Atlas Pricing",
                description="Duplicate",
                created_at=utc_now(),
                updated_at=utc_now(),
            )
        )
        assert duplicate_topic.id == topic.id

        memory = repository.create_memory(
            Memory(
                id=new_id(),
                workspace_id=workspace_id,
                topic_id=topic.id,
                topic_name=topic.name,
                message_id=message.id,
                content="For Atlas pricing, test quarterly billing.",
                memory_type=MemoryType.task,
                confidence=0.9,
                created_at=utc_now(),
                source="web",
                source_url="https://example.test/source",
                source_timestamp=created_at,
                approximate_token_count=7,
            )
        )

        topics = repository.list_topics(workspace_id)
        assert len(topics) == 1
        assert topics[0].memory_count == 1
        assert repository.get_topic(workspace_id, topic.id).name == "Atlas Pricing"
        assert repository.find_topic_by_id(workspace_id, topic.id).id == topic.id
        assert repository.get_topic("wrong-workspace", topic.id) is None

        by_message = repository.list_memories_for_message(message.id)
        by_topic = repository.list_memories_for_topic(workspace_id, topic.id)
        search = repository.search_memories(workspace_id, "Atlas pricing", [], limit=10)
        filtered_search = repository.search_memories(workspace_id, "Atlas pricing", [topic.id], limit=10)
        excluded_search = repository.search_memories(workspace_id, "Atlas pricing", [new_id()], limit=10)

        assert [item.id for item in by_message] == [memory.id]
        assert [item.id for item in by_topic] == [memory.id]
        assert [item.id for item in search] == [memory.id]
        assert [item.id for item in filtered_search] == [memory.id]
        assert excluded_search == []
    finally:
        repository.reset_workspace(workspace_id)

    assert repository.list_topics(workspace_id) == []
