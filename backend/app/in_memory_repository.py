from __future__ import annotations

from backend.app.domain import Conversation, Galaxy, Memory, Message, Topic, Workspace, new_id, utc_now
from backend.app.repository import MemoryRepository


class InMemoryMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self.workspaces: dict[str, Workspace] = {}
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, Message] = {}
        self.galaxies: dict[str, Galaxy] = {}
        self.topics: dict[str, Topic] = {}
        self.memories: dict[str, Memory] = {}

    def ensure_workspace(self, workspace_id: str, name: str | None = None) -> Workspace:
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = Workspace(workspace_id, name or workspace_id, utc_now())
        return self.workspaces[workspace_id]

    def get_or_create_conversation(self, workspace_id: str, external_id: str, source: str) -> Conversation:
        for conversation in self.conversations.values():
            if conversation.workspace_id == workspace_id and conversation.external_id == external_id and conversation.source == source:
                return conversation
        conversation = Conversation(new_id(), workspace_id, external_id, source, utc_now())
        self.conversations[conversation.id] = conversation
        return conversation

    def find_message(self, workspace_id: str, source: str, external_id: str) -> Message | None:
        return next(
            (
                message
                for message in self.messages.values()
                if message.workspace_id == workspace_id and message.source == source and message.external_id == external_id
            ),
            None,
        )

    def create_message(self, message: Message) -> Message:
        self.messages[message.id] = message
        return message

    def update_message_status(self, message_id: str, status: str) -> None:
        message = self.messages[message_id]
        self.messages[message_id] = Message(
            **{**message.__dict__, "processing_status": status, "processed_at": utc_now() if status in {"processed", "failed"} else None}
        )

    def get_or_create_galaxy(self, workspace_id: str, name: str, description: str) -> Galaxy:
        for galaxy in self.galaxies.values():
            if galaxy.workspace_id == workspace_id and galaxy.name == name:
                return galaxy
        galaxy = Galaxy(new_id(), workspace_id, name, description, utc_now(), utc_now())
        self.galaxies[galaxy.id] = galaxy
        return galaxy

    def list_topics(self, workspace_id: str) -> list[Topic]:
        return [self._with_count(topic) for topic in self.topics.values() if topic.workspace_id == workspace_id]

    def get_topic(self, workspace_id: str, topic_id: str) -> Topic | None:
        topic = self.topics.get(topic_id)
        if topic is None or topic.workspace_id != workspace_id:
            return None
        return self._with_count(topic)

    def find_topic_by_id(self, workspace_id: str, topic_id: str) -> Topic | None:
        return self.get_topic(workspace_id, topic_id)

    def create_topic(self, topic: Topic) -> Topic:
        for existing in self.topics.values():
            if (
                existing.workspace_id == topic.workspace_id
                and existing.galaxy_id == topic.galaxy_id
                and existing.name == topic.name
            ):
                return self._with_count(existing)
        self.topics[topic.id] = topic
        return topic

    def create_memory(self, memory: Memory) -> Memory:
        self.memories[memory.id] = memory
        return memory

    def list_memories_for_message(self, message_id: str) -> list[Memory]:
        return [memory for memory in self.memories.values() if memory.message_id == message_id]

    def list_memories_for_topic(self, workspace_id: str, topic_id: str) -> list[Memory]:
        return [
            memory
            for memory in self.memories.values()
            if memory.workspace_id == workspace_id and memory.topic_id == topic_id
        ]

    def search_memories(self, workspace_id: str, query: str, topic_ids: list[str], limit: int) -> list[Memory]:
        terms = {term.lower() for term in query.split()}
        results = [
            memory
            for memory in self.memories.values()
            if memory.workspace_id == workspace_id
            and (not topic_ids or memory.topic_id in topic_ids)
            and terms & {term.strip(".,!?").lower() for term in memory.content.split()}
        ]
        return results[:limit]

    def reset_workspace(self, workspace_id: str) -> None:
        topic_ids = {topic.id for topic in self.topics.values() if topic.workspace_id == workspace_id}
        message_ids = {message.id for message in self.messages.values() if message.workspace_id == workspace_id}
        self.memories = {key: value for key, value in self.memories.items() if value.workspace_id != workspace_id}
        self.topics = {key: value for key, value in self.topics.items() if key not in topic_ids}
        self.messages = {key: value for key, value in self.messages.items() if key not in message_ids}
        self.conversations = {key: value for key, value in self.conversations.items() if value.workspace_id != workspace_id}
        self.galaxies = {key: value for key, value in self.galaxies.items() if value.workspace_id != workspace_id}
        self.workspaces.pop(workspace_id, None)

    def _with_count(self, topic: Topic) -> Topic:
        count = sum(1 for memory in self.memories.values() if memory.topic_id == topic.id)
        return Topic(**{**topic.__dict__, "memory_count": count})
