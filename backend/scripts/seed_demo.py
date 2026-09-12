from __future__ import annotations

from backend.app.config import get_settings
from backend.app.llm import HeuristicLLMClient
from backend.app.repository import PostgresMemoryRepository
from backend.app.seed_data import seed_demo
from backend.app.service import MemoryEngine


def main() -> None:
    settings = get_settings()
    engine = MemoryEngine(PostgresMemoryRepository(settings.database_url), HeuristicLLMClient())
    response = seed_demo(engine)
    print(f"Seeded {response.memories_created} memories across {response.topics_created} topics.")


if __name__ == "__main__":
    main()
