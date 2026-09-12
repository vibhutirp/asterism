from functools import lru_cache

from backend.app.config import get_settings
from backend.app.llm import HeuristicLLMClient
from backend.app.repository import PostgresMemoryRepository
from backend.app.service import MemoryEngine


@lru_cache
def get_memory_engine() -> MemoryEngine:
    settings = get_settings()
    repository = PostgresMemoryRepository(settings.database_url)
    llm = HeuristicLLMClient()
    return MemoryEngine(repository=repository, llm=llm, default_context_tokens=settings.default_context_tokens)
