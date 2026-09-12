from __future__ import annotations

import json
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


_MEMORY_TYPES = [item.value for item in MemoryType]

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "memories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_type": {"type": "string", "enum": _MEMORY_TYPES},
                    "confidence": {"type": "number"},
                    "suggested_topic_name": {"type": "string"},
                    "suggested_topic_description": {"type": "string"},
                    "suggested_galaxy_name": {"type": "string"},
                    "suggested_galaxy_description": {"type": "string"},
                },
                "required": [
                    "content",
                    "memory_type",
                    "confidence",
                    "suggested_topic_name",
                    "suggested_topic_description",
                    "suggested_galaxy_name",
                    "suggested_galaxy_description",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["memories"],
    "additionalProperties": False,
}

_CHOOSE_TOPIC_SCHEMA = {
    "type": "object",
    "properties": {"topic_id": {"type": ["string", "null"]}},
    "required": ["topic_id"],
    "additionalProperties": False,
}

_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "insufficient_context": {"type": "boolean"},
    },
    "required": ["answer", "insufficient_context"],
    "additionalProperties": False,
}

_EXTRACTION_SYSTEM_PROMPT = """You extract atomic memories from a single message for a personal memory system.

Rules:
- Split unrelated ideas into separate memories. Keep closely related details of one idea together in one memory.
- Classify each memory as exactly one of: fact, idea, decision, question, task, preference, observation. \
A suggestion or proposal is an idea, not a decision; only an explicit commitment or resolution is a decision. \
Open deliberation ("debating whether", "thinking about", "considering") is a question or idea, never a \
decision. Something the user needs to do is a task. A like/dislike/wish is a preference.
- Preserve the user's wording. Apply only light cleanup (capitalization, punctuation, making a fragment a \
complete sentence). Never add details, never invent facts, never speculate beyond the message.
- For each memory propose: a concise suggested_topic_name (2-4 words, specific, reusable across related \
memories), a one-sentence suggested_topic_description, a suggested_galaxy_name that is a broad category \
(e.g. Product, Personal, Career, Tech), and a one-sentence suggested_galaxy_description.
- confidence is a number between 0 and 1 for how confident you are in the extraction and classification.
- If the message contains nothing worth remembering, return an empty memories list."""

_CHOOSE_TOPIC_SYSTEM_PROMPT = """You assign a new memory to an existing topic or decide a new topic is needed.

Rules:
- Same subject => reuse the existing topic, even if the specific sub-idea differs. Another idea, task, or \
detail about a subject that already has a topic belongs in that topic (e.g. another Atlas signup idea \
belongs to an existing "Atlas Onboarding" topic, not a new "Signup improvements" topic; a new suggestion \
about the same product's invoices belongs to the existing invoice topic even if it proposes something new).
- Do NOT merge topics just because they share generic words like "ideas", "plan", "notes", or a company name \
used in a different context.
- Only when no existing topic covers the memory's subject, return null so a new topic is created.
- Return only an id from the provided candidate list, or null. Never invent an id."""

_ANSWER_SYSTEM_PROMPT = """You answer a question using ONLY the provided stored memories.

Rules:
- Base every claim strictly on the provided memories. Never use outside knowledge, never fabricate, never \
guess beyond what the memories state.
- If the memories do not contain the information needed to answer, set insufficient_context to true and \
reply politely that there is not enough stored context to answer.
- When the memories do contain the answer, answer concisely and set insufficient_context to false."""

_INSUFFICIENT_CONTEXT_ANSWER = "I do not have enough stored context to answer that."


class OpenRouterLLMClient(LLMClient):
    """LLM adapter backed by OpenRouter (OpenAI-compatible API) with structured outputs."""

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini", client=None):
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        self.client = client
        self.model = model

    def extract_memories(self, message: str) -> list[ExtractedMemory]:
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                payload = self._complete_json(
                    system=_EXTRACTION_SYSTEM_PROMPT,
                    user=message,
                    schema_name="memory_extraction",
                    schema=_EXTRACTION_SCHEMA,
                )
                return [self._validate_memory(item) for item in payload["memories"]]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                last_error = exc
        raise ValueError(f"OpenRouter memory extraction returned invalid output: {last_error}")

    def choose_topic(self, memory: ExtractedMemory, candidates: list[TopicCandidate]) -> str | None:
        if not candidates:
            return None
        candidate_lines = "\n".join(
            f"- id: {candidate.id} | name: {candidate.name} | galaxy: {candidate.galaxy_name} | description: {candidate.description}"
            for candidate in candidates
        )
        user = (
            f"Memory: {memory.content}\n"
            f"Memory type: {memory.memory_type.value}\n"
            f"Suggested topic name: {memory.suggested_topic_name}\n"
            f"Suggested topic description: {memory.suggested_topic_description}\n\n"
            f"Existing topics:\n{candidate_lines}"
        )
        try:
            payload = self._complete_json(
                system=_CHOOSE_TOPIC_SYSTEM_PROMPT,
                user=user,
                schema_name="topic_choice",
                schema=_CHOOSE_TOPIC_SCHEMA,
            )
            topic_id = payload["topic_id"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
        if topic_id in {candidate.id for candidate in candidates}:
            return topic_id
        return None

    def answer_from_context(self, query: str, context: list[str]) -> tuple[str, bool]:
        if not context:
            return _INSUFFICIENT_CONTEXT_ANSWER, True
        memory_lines = "\n".join(f"- {item}" for item in context)
        user = f"Question: {query}\n\nStored memories:\n{memory_lines}"
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                payload = self._complete_json(
                    system=_ANSWER_SYSTEM_PROMPT,
                    user=user,
                    schema_name="grounded_answer",
                    schema=_ANSWER_SCHEMA,
                )
                answer = payload["answer"]
                insufficient = payload["insufficient_context"]
                if not isinstance(answer, str) or not isinstance(insufficient, bool):
                    raise ValueError("answer must be a string and insufficient_context a boolean")
                if insufficient or not answer.strip():
                    return _INSUFFICIENT_CONTEXT_ANSWER, True
                return answer, False
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                last_error = exc
        raise ValueError(f"OpenRouter grounded answer returned invalid output: {last_error}")

    def _complete_json(self, system: str, user: str, schema_name: str, schema: dict) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
        )
        # Not every model behind OpenRouter honors response_format; some wrap
        # the JSON in markdown code fences instead.
        return json.loads(_strip_code_fences(response.choices[0].message.content))

    def _validate_memory(self, item: dict) -> ExtractedMemory:
        content = item["content"]
        memory_type = item["memory_type"]
        confidence = item["confidence"]
        topic_name = item["suggested_topic_name"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("memory content must be a non-empty string")
        if memory_type not in _MEMORY_TYPES:
            raise ValueError(f"memory_type must be one of {_MEMORY_TYPES}")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be a number between 0 and 1")
        if not isinstance(topic_name, str) or not topic_name.strip():
            raise ValueError("suggested_topic_name must be a non-empty string")
        return ExtractedMemory(
            content=content.strip(),
            memory_type=MemoryType(memory_type),
            confidence=float(confidence),
            suggested_topic_name=topic_name.strip(),
            suggested_topic_description=str(item["suggested_topic_description"]).strip(),
            suggested_galaxy_name=str(item["suggested_galaxy_name"]).strip() or "Personal",
            suggested_galaxy_description=str(item["suggested_galaxy_description"]).strip(),
        )


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?\s*```$", stripped, flags=re.DOTALL)
    return match.group(1) if match else stripped


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _clean_memory_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned.endswith((".", "?", "!")):
        cleaned += "."
    return cleaned[0].upper() + cleaned[1:]
