from functools import lru_cache

from backend.app.config import Settings, get_settings
from backend.app.llm import HeuristicLLMClient, LLMClient, OpenRouterLLMClient
from backend.app.repository import PostgresMemoryRepository
from backend.app.service import MemoryEngine


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.openrouter_api_key:
        return OpenRouterLLMClient(api_key=settings.openrouter_api_key, model=settings.openrouter_model)
    return HeuristicLLMClient()


@lru_cache
def get_memory_engine() -> MemoryEngine:
    settings = get_settings()
    repository = PostgresMemoryRepository(settings.database_url)
    llm = build_llm_client(settings)
    return MemoryEngine(repository=repository, llm=llm, default_context_tokens=settings.default_context_tokens)
