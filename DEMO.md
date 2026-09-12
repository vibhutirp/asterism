# Asterism — Demo Runbook

Cold start to demo-ready, in order. Run everything from the repo root unless noted.

## 0. One-time setup

```bash
# Python deps
python -m pip install -r backend/requirements.txt

# Frontend deps
cd frontend && npm ci && cd ..

# Environment: copy the example and fill in the OpenRouter key
cp .env.example .env         # set OPENROUTER_API_KEY=sk-or-v1-... (required for real extraction)

# Frontend env: api mode via the Vite dev proxy
printf 'VITE_DATA_MODE=api\nVITE_WORKSPACE_ID=demo\nAPI_TARGET=http://127.0.0.1:8000\n' > frontend/.env.local

# Postgres container (first time only; later use `docker start asterism-pg`)
docker run -d --name asterism-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=asterism -p 5432:5432 postgres:16
```

## 1. Cold start (every demo)

```bash
docker start asterism-pg                      # Postgres up
python -m backend.scripts.migrate             # apply schema (idempotent)
uvicorn backend.app.main:app --port 8000      # API on :8000 (leave running)
```

In a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/reset-demo   # clean demo workspace + LLM-seeded data
cd frontend && npm run dev                          # frontend on http://localhost:5173
```

Open http://localhost:5173 — the header should read "Connected data" with 4 topics.

Optional Slack ingestion (only if SLACK_BOT_TOKEN / SLACK_APP_TOKEN are set in .env —
see backend/README.md "Slack setup"):

```bash
python -m backend.scripts.run_slack
```

## 2. Demo script (4 steps)

1. **Mixed message → topics appear.** In the panel at bottom-left, paste one message with
   unrelated ideas, e.g. *"We should redesign the invoice PDF for Bloom clients. Also I want
   to start running twice a week before the May marathon."* Click **Save memory** — the
   confirmation lists the topics it was organized into, and new nodes appear in the universe.
2. **Related follow-up → node grows.** Send *"Another Bloom invoice thought: show tax per
   line item in the totals."* — the existing invoice topic's memory count grows instead of a
   duplicate topic appearing.
3. **Click a topic → sources.** Click any node (or use List view): the inspector shows the
   topic's galaxy, overview, and each memory with its type and "Received ..." source
   provenance from the original message.
4. **Ask → grounded answer.** Type *"What onboarding improvements have we discussed for
   Atlas?"* and click **Ask** — the answer is grounded in stored memories only, with a
   "Grounded in N stored memories" count. Asking about something never mentioned returns a
   friendly "not enough stored context" state instead of a made-up answer.

## Notes

- Ingestion is idempotent on (workspace, source, externalId) — Slack retries and repeated
  sends of the same event never duplicate memories.
- `POST /api/reset-demo` only touches the `demo` workspace; re-run it any time to restore a
  clean state (it re-extracts seed messages through the live LLM, so names can vary slightly).
- Full API shapes: backend/API_CONTRACT.md. PRD acceptance suite:
  `python -m backend.scripts.acceptance` (requires OPENROUTER_API_KEY and Postgres).
