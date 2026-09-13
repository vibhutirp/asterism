# Asterism — Secondary Brain

Asterism is a conversational memory layer. It ingests messages (web, Slack DMs, seeds),
uses an LLM to extract atomic memories and organize them into topics and galaxies, persists
everything with provenance in Postgres, and answers questions grounded strictly in stored
context — saying "not enough stored context" instead of inventing answers.

Product background, target users, and market context: [docs/PRODUCT.md](docs/PRODUCT.md).
Demo runbook (cold start to demo-ready): [DEMO.md](DEMO.md).

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

- `backend/app/` — FastAPI app: `service.py` (MemoryEngine pipeline), `llm.py`
  (OpenRouter client with structured outputs + heuristic fallback), `repository.py`
  (Postgres), `slack_adapter.py` (DM-only Socket Mode ingestion).
- `frontend/` — React "Observatory": 3D topic universe, topic inspector, ask/capture panel.
  See [frontend/README.md](frontend/README.md).
- `db/migrations/` — SQL schema, applied by `backend/scripts/migrate.py`.
- Full request/response shapes: [backend/API_CONTRACT.md](backend/API_CONTRACT.md).

## Prerequisites

- Python 3.11+ (`python -m pip install -r backend/requirements.txt`)
- Docker (for Postgres 16)
- Node 22+ (only for the frontend)
- An [OpenRouter](https://openrouter.ai) API key for real LLM extraction. Without a key the
  backend falls back to a deterministic heuristic client meant for tests only.

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

DM-only ingestion over Socket Mode; requires `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`.
Setup steps (scopes `im:history`, `chat:write`; bot event `message.im`) are in
[backend/README.md](backend/README.md).

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

- Single-workspace demo model: everything defaults to the `demo` workspace; no auth or
  multi-tenant separation.
- Retrieval is Postgres full-text (OR-of-terms, ranked), not semantic/embedding search.
- The Slack adapter is DM-only and hardcodes the `demo` workspace.
- Topic and galaxy names come from the LLM, so reseeding can produce slightly different
  names run to run (structure is stable, names vary).
- The frontend's 10-second polling is the only live-update mechanism (no websockets).
