from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.config import Settings
from backend.app.dependencies import build_llm_client
from backend.app.domain import ExtractedMemory
from backend.app.llm import HeuristicLLMClient, OpenRouterLLMClient, TopicCandidate
from backend.app.models import MemoryType


class FakeOpenAI:
    """Stands in for the OpenAI-compatible client; returns canned message contents in order."""

    def __init__(self, contents: list[str]):
        self.calls: list[dict] = []
        self._contents = list(contents)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        content = self._contents.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def make_client(contents: list[str]) -> tuple[OpenRouterLLMClient, FakeOpenAI]:
    fake = FakeOpenAI(contents)
    return OpenRouterLLMClient(api_key="test-key", model="test-model", client=fake), fake


def extraction_payload(**overrides) -> str:
    memory = {
        "content": "Remove phone number from Atlas signup.",
        "memory_type": "idea",
        "confidence": 0.9,
        "suggested_topic_name": "Atlas Onboarding",
        "suggested_topic_description": "Onboarding improvements for Atlas.",
        "suggested_galaxy_name": "Product",
        "suggested_galaxy_description": "Product ideas and improvements.",
    }
    memory.update(overrides)
    return json.dumps({"memories": [memory]})


def sample_memory() -> ExtractedMemory:
    return ExtractedMemory(
        content="Another Atlas signup idea: let people explore first.",
        memory_type=MemoryType.idea,
        confidence=0.8,
        suggested_topic_name="Atlas Signup Ideas",
        suggested_topic_description="Signup ideas.",
        suggested_galaxy_name="Product",
        suggested_galaxy_description="Product work.",
    )


CANDIDATES = [
    TopicCandidate(id="t-onboarding", name="Atlas Onboarding", description="Signup work", galaxy_name="Product"),
    TopicCandidate(id="t-pricing", name="Atlas Pricing", description="Pricing work", galaxy_name="Product"),
]


def test_extract_memories_parses_and_validates_structured_output() -> None:
    llm, fake = make_client([extraction_payload()])

    memories = llm.extract_memories("For Atlas, remove phone number from signup.")

    assert len(memories) == 1
    assert memories[0].content == "Remove phone number from Atlas signup."
    assert memories[0].memory_type == MemoryType.idea
    assert memories[0].confidence == 0.9
    assert fake.calls[0]["model"] == "test-model"
    assert fake.calls[0]["response_format"]["type"] == "json_schema"
    assert fake.calls[0]["response_format"]["json_schema"]["strict"] is True


@pytest.mark.parametrize("fence", ["```json", "```"])
def test_extract_memories_strips_markdown_code_fences(fence: str) -> None:
    llm, _ = make_client([f"{fence}\n{extraction_payload()}\n```"])

    memories = llm.extract_memories("For Atlas, remove phone number from signup.")

    assert len(memories) == 1
    assert memories[0].content == "Remove phone number from Atlas signup."


def test_extract_memories_invalid_json_retries_then_raises_value_error() -> None:
    llm, fake = make_client(["not json at all", "{still: not json"])

    with pytest.raises(ValueError, match="invalid output"):
        llm.extract_memories("hello")

    assert len(fake.calls) == 2


def test_extract_memories_recovers_when_retry_returns_valid_output() -> None:
    llm, fake = make_client(["not json at all", extraction_payload()])

    memories = llm.extract_memories("hello")

    assert len(memories) == 1
    assert len(fake.calls) == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"confidence": 1.7},
        {"content": "   "},
        {"suggested_topic_name": ""},
        {"memory_type": "musing"},
    ],
)
def test_extract_memories_rejects_out_of_contract_fields(overrides: dict) -> None:
    llm, fake = make_client([extraction_payload(**overrides), extraction_payload(**overrides)])

    with pytest.raises(ValueError, match="invalid output"):
        llm.extract_memories("hello")

    assert len(fake.calls) == 2


def test_choose_topic_returns_candidate_id() -> None:
    llm, fake = make_client([json.dumps({"topic_id": "t-onboarding"})])

    chosen = llm.choose_topic(sample_memory(), CANDIDATES)

    assert chosen == "t-onboarding"
    assert "t-onboarding" in fake.calls[0]["messages"][1]["content"]


def test_choose_topic_rejects_id_not_in_candidate_list() -> None:
    llm, _ = make_client([json.dumps({"topic_id": "t-invented"})])

    assert llm.choose_topic(sample_memory(), CANDIDATES) is None


def test_choose_topic_null_and_unparseable_mean_create_new() -> None:
    llm_null, _ = make_client([json.dumps({"topic_id": None})])
    llm_bad, _ = make_client(["garbage output"])

    assert llm_null.choose_topic(sample_memory(), CANDIDATES) is None
    assert llm_bad.choose_topic(sample_memory(), CANDIDATES) is None


def test_choose_topic_without_candidates_skips_api_call() -> None:
    llm, fake = make_client([])

    assert llm.choose_topic(sample_memory(), []) is None
    assert fake.calls == []


def test_answer_from_context_empty_context_short_circuits() -> None:
    llm, fake = make_client([])

    answer, insufficient = llm.answer_from_context("What about payroll?", [])

    assert insufficient is True
    assert "not" in answer and "context" in answer
    assert fake.calls == []


def test_answer_from_context_returns_grounded_answer() -> None:
    llm, fake = make_client([json.dumps({"answer": "Remove phone number from signup.", "insufficient_context": False})])

    answer, insufficient = llm.answer_from_context(
        "What signup changes for Atlas?", ["Remove phone number from Atlas signup."]
    )

    assert insufficient is False
    assert answer == "Remove phone number from signup."
    assert "Remove phone number from Atlas signup." in fake.calls[0]["messages"][1]["content"]


def test_answer_from_context_respects_insufficient_flag() -> None:
    llm, _ = make_client([json.dumps({"answer": "", "insufficient_context": True})])

    answer, insufficient = llm.answer_from_context("payroll?", ["Atlas signup memory."])

    assert insufficient is True
    assert answer == "I do not have enough stored context to answer that."


def test_answer_from_context_invalid_output_retries_then_raises() -> None:
    llm, fake = make_client(["nope", "still nope"])

    with pytest.raises(ValueError, match="invalid output"):
        llm.answer_from_context("query", ["memory"])

    assert len(fake.calls) == 2


def test_build_llm_client_selects_openrouter_only_when_key_is_set() -> None:
    with_key = Settings(OPENROUTER_API_KEY="sk-or-test", OPENROUTER_MODEL="anthropic/claude-sonnet-5", _env_file=None)
    without_key = Settings(OPENROUTER_API_KEY=None, _env_file=None)
    empty_key = Settings(OPENROUTER_API_KEY="", _env_file=None)

    openrouter_client = build_llm_client(with_key)
    assert isinstance(openrouter_client, OpenRouterLLMClient)
    assert openrouter_client.model == "anthropic/claude-sonnet-5"
    assert isinstance(build_llm_client(without_key), HeuristicLLMClient)
    assert isinstance(build_llm_client(empty_key), HeuristicLLMClient)
