# Asterism Memory

Asterism Memory is a local-first conversational memory agent that turns scattered messages into organized, source-backed knowledge. It captures small "atomic memories" from conversations, groups them into meaningful topics and galaxies, and answers questions only from stored context — it helps people and teams remember what was said, why it mattered, and where it came from.

## The problem

Imagine trying to find one important decision in a busy Slack channel. You remember someone said it last week, but not the exact words. You scroll threads, try a few keyword searches, open old messages — and still have to reconstruct the answer yourself. The same thing happens with AI-agent chats, where product strategy, database setup, and test coverage all blur into one long thread. People rarely lose context because they lack information; they lose it because information is scattered, duplicated, buried, or disconnected from its source:

- Decisions are made in chat but never copied into documentation.
- Ideas are repeated because nobody remembers where they were discussed.
- Search returns long threads, not clear answers.
- AI assistants summarize confidently without showing their evidence.

## What Asterism does

- **Automatic memory capture** — an LLM splits each message into focused, atomic memories (idea, decision, task, question, preference, fact, observation).
- **Topic & galaxy organization** — memories are grouped into topics ("Atlas Onboarding", "Camping Trip") inside broader galaxies ("Product", "Personal"); related follow-ups reuse the existing topic instead of spawning near-duplicates.
- **Source-backed recall** — every memory keeps provenance (message, source, timestamp, permalink), so answers can be traced to the original conversation.
- **Grounded question answering** — answers come only from retrieved stored memories, and the system says "I don't have enough stored context" instead of inventing one.
- **Duplicate-safe ingestion** — repeated deliveries of the same external event (Slack retries included) never create duplicate memories.
- **A 3D knowledge universe** — the React frontend renders topics as galaxy-grouped star clouds you can explore, inspect, and query.

## See it in action

Send one mixed message:

> "For Atlas, remove phone number from signup. Separately I want to plan a camping trip."

Asterism stores two memories under two different topics in two different galaxies. Ask later — *"What onboarding improvements have we discussed for Atlas?"* — and it answers from those stored memories with a "grounded in N memories" citation, never from general knowledge.

Full product context — target users, user stories, market analysis, roadmap: [docs/PRODUCT.md](docs/PRODUCT.md). Demo runbook: [DEMO.md](DEMO.md).

---

## Architecture

```
message (web / Slack / seed)
  └─> POST /api/messages          idempotent on (workspace, source, externalId)
        └─> LLM extraction        split into atomic memories, typed + confidence
              └─> topic assignment  reuse an existing topic or create one (galaxy-grouped)
                    └─> Postgres     memories + topics + galaxies + full provenance
                          └─> retrieval   ranked full-text search, token-budgeted
                                └─> POST /api/query   grounded answer, or insufficientContext
```

- `backend/app/` — FastAPI app: `service.py` (MemoryEngine pipeline), `llm.py` (OpenRouter client with structured outputs + heuristic fallback), `repository.py` (Postgres), `slack_adapter.py` (DM-only Socket Mode ingestion).
- `frontend/` — React "Observatory": 3D topic universe, topic inspector, ask/capture panel. See [frontend/README.md](frontend/README.md).
- `db/migrations/` — SQL schema, applied by `backend/scripts/migrate.py`.
- Full request/response shapes: [backend/API_CONTRACT.md](backend/API_CONTRACT.md).

## Prerequisites

- Python 3.11+ (`python -m pip install -r backend/requirements.txt`)
- Docker (for Postgres 16)
- Node 22+ (only for the frontend)
- An [OpenRouter](https://openrouter.ai) API key for real LLM extraction. Without a key the backend falls back to a deterministic heuristic client meant for tests only.

## Environment variables

Copy `.env.example` to `.env` (never commit `.env`):

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | yes | Postgres connection string |
| `OPENROUTER_API_KEY` | for real LLM | OpenRouter key; unset = heuristic test client |
| `OPENROUTER_MODEL` | no | Provider-prefixed model, default `openai/gpt-4o-mini` |
| `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` | no | Only for the optional Slack DM adapter |

## Database setup

```bash
docker run -d --name asterism-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=asterism -p 5432:5432 postgres:16
python -m backend.scripts.migrate
```

(Afterwards `docker start asterism-pg` is enough.)

## Run the server

```bash
uvicorn backend.app.main:app --port 8000
```

Interactive docs at http://127.0.0.1:8000/docs.

## Seed / reset demo data

```bash
python -m backend.scripts.seed_demo            # seed the demo workspace once
curl -X POST http://127.0.0.1:8000/api/reset-demo   # or wipe + reseed via the API
```

## API endpoints

`GET /api/health` — liveness:

```bash
curl http://127.0.0.1:8000/api/health
```

`POST /api/messages` — ingest a message; extracts memories and assigns topics:

```bash
curl -X POST http://127.0.0.1:8000/api/messages -H "Content-Type: application/json" -d '{
  "workspaceId": "demo", "conversationId": "c1", "externalId": "evt-1", "role": "user",
  "content": "For Atlas, remove phone number from signup. Separately, plan a camping trip.",
  "source": "web", "sourceUrl": null }'
```

`GET /api/topics` — visualization-ready topic list:

```bash
curl "http://127.0.0.1:8000/api/topics?workspaceId=demo"
```

`GET /api/topics/{id}` — topic detail with memories and source provenance:

```bash
curl "http://127.0.0.1:8000/api/topics/<topic-id>?workspaceId=demo"
```

`POST /api/query` — grounded Q&A over retrieved memories only:

```bash
curl -X POST http://127.0.0.1:8000/api/query -H "Content-Type: application/json" -d '{
  "workspaceId": "demo", "query": "What onboarding improvements have we discussed for Atlas?",
  "maxContextTokens": 2000, "topicIds": [] }'
```

`POST /api/reset-demo` — reset and reseed only the `demo` workspace:

```bash
curl -X POST http://127.0.0.1:8000/api/reset-demo
```

## Frontend

```bash
cd frontend
npm ci
printf 'VITE_DATA_MODE=api\nVITE_WORKSPACE_ID=demo\nAPI_TARGET=http://127.0.0.1:8000\n' > .env.local
npm run dev    # http://localhost:5173
```

## Slack adapter (optional)

DM-only ingestion over Socket Mode; requires `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`. Setup steps (scopes `im:history`, `chat:write`; bot event `message.im`) are in [backend/README.md](backend/README.md).

```bash
python -m backend.scripts.run_slack
```

## Tests

```bash
python -m pytest backend_tests        # unit + integration (Postgres tests skip if no DB)
python -m backend.scripts.acceptance  # PRD acceptance vs the LIVE LLM (needs key + Postgres)
cd frontend && npm test && npm run typecheck
```

## Known limitations

- Single-workspace demo model: everything defaults to the `demo` workspace; no auth or multi-tenant separation.
- Retrieval is Postgres full-text (OR-of-terms, ranked), not semantic/embedding search.
- The Slack adapter is DM-only and hardcodes the `demo` workspace.
- Topic and galaxy names come from the LLM, so reseeding can produce slightly different names run to run (structure is stable, names vary).
- The frontend's 10-second polling is the only live-update mechanism (no websockets).
