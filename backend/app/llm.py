from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.domain import ExtractedMemory
from backend.app.models import MemoryType


@dataclass(frozen=True)
class TopicCandidate:
    id: str
    name: str
    description: str
    galaxy_name: str


class LLMClient:
    def extract_memories(self, message: str) -> list[ExtractedMemory]:
        raise NotImplementedError

    def choose_topic(self, memory: ExtractedMemory, candidates: list[TopicCandidate]) -> str | None:
        raise NotImplementedError

    def answer_from_context(self, query: str, context: list[str]) -> tuple[str, bool]:
        raise NotImplementedError


class HeuristicLLMClient(LLMClient):
    """Deterministic local adapter used until a hosted LLM is configured."""

    def extract_memories(self, message: str) -> list[ExtractedMemory]:
        parts = [
            part.strip(" .")
            for part in re.split(r"\b(?:separately|also|and|another)\b|[.;]\s*", message, flags=re.IGNORECASE)
            if part.strip(" .")
        ]
        memories = [self._memory_from_text(part) for part in parts]
        return memories or [self._memory_from_text(message.strip())]

    def choose_topic(self, memory: ExtractedMemory, candidates: list[TopicCandidate]) -> str | None:
        desired = _normalize(memory.suggested_topic_name)
        for candidate in candidates:
            if _normalize(candidate.name) == desired:
                return candidate.id
        desired_terms = set(desired.split())
        for candidate in candidates:
            candidate_terms = set(_normalize(candidate.name).split())
            if desired_terms and len(desired_terms & candidate_terms) >= min(2, len(desired_terms)):
                return candidate.id
        return None

    def answer_from_context(self, query: str, context: list[str]) -> tuple[str, bool]:
        if not context:
            return "I do not have enough stored context to answer that.", True
        query_terms = set(_normalize(query).split())
        supported = [item for item in context if query_terms & set(_normalize(item).split())]
        if not supported:
            return "I do not have enough stored context to answer that.", True
        return " ".join(supported[:4]), False

    def _memory_from_text(self, text: str) -> ExtractedMemory:
        lowered = text.lower()
        topic_name = "General Notes"
        topic_description = "General captured memories."
        galaxy_name = "Personal"
        galaxy_description = "Personal notes and plans."

        if "atlas" in lowered and ("signup" in lowered or "onboarding" in lowered or "phone" in lowered):
            topic_name = "Atlas Onboarding"
            topic_description = "Signup, activation, and onboarding improvements for Atlas."
            galaxy_name = "Product"
            galaxy_description = "Product ideas, pricing, launch, and customer experience."
        elif "atlas" in lowered and ("price" in lowered or "pricing" in lowered or "annual" in lowered):
            topic_name = "Atlas Pricing"
            topic_description = "Atlas pricing, packaging, and monetization ideas."
            galaxy_name = "Product"
            galaxy_description = "Product ideas, pricing, launch, and customer experience."
        elif "launch" in lowered:
            topic_name = "Launch"
            topic_description = "Launch planning and go-to-market notes."
            galaxy_name = "Product"
            galaxy_description = "Product ideas, pricing, launch, and customer experience."
        elif "camp" in lowered or "trip" in lowered:
            topic_name = "Camping Trip"
            topic_description = "Camping trip plans, preferences, and tasks."

        memory_type = MemoryType.idea
        if "?" in text:
            memory_type = MemoryType.question
        elif re.search(r"\b(todo|task|need to|should test|plan)\b", lowered):
            memory_type = MemoryType.task
        elif re.search(r"\b(decided|decision|will)\b", lowered):
            memory_type = MemoryType.decision
        elif re.search(r"\b(prefer|like|want)\b", lowered):
            memory_type = MemoryType.preference

        return ExtractedMemory(
            content=_clean_memory_text(text),
            memory_type=memory_type,
            confidence=0.82,
            suggested_topic_name=topic_name,
            suggested_topic_description=topic_description,
            suggested_galaxy_name=galaxy_name,
            suggested_galaxy_description=galaxy_description,
        )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _clean_memory_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned.endswith((".", "?", "!")):
        cleaned += "."
    return cleaned[0].upper() + cleaned[1:]
