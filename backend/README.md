# Asterism Memory Backend

Python/FastAPI backend for the conversational memory engine.

## Install

```bash
python -m pip install -r backend/requirements.txt
```

## Configure

Set `DATABASE_URL`:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asterism
```

## Migrate

```bash
python -m backend.scripts.migrate
```

## Seed Demo Data

```bash
python -m backend.scripts.seed_demo
```

## Run

```bash
python -m uvicorn backend.app.main:app --reload
```

## Test

```bash
python -m pytest backend_tests
```

## Slack setup

DM-only ingestion via Socket Mode (no public URL needed):

1. Create an app at https://api.slack.com/apps ("From scratch"), pick your workspace.
2. **Socket Mode**: enable it; generate an app-level token with the `connections:write`
   scope. That token is `SLACK_APP_TOKEN` (`xapp-...`).
3. **OAuth & Permissions**: add bot token scopes `im:history` and `chat:write`,
   then install the app to the workspace. The bot token is `SLACK_BOT_TOKEN` (`xoxb-...`).
4. **Event Subscriptions**: enable events and subscribe to the bot event `message.im`.
5. Set both tokens in the environment (or `.env`), then run:

```bash
python -m backend.scripts.run_slack
```

DM the bot to store memories ("Organized that into N topic(s): ..."); start a
message with `ask:` to query instead. Bot/self messages and edits are ignored,
and Slack retry deliveries are absorbed by externalId idempotency.

## Endpoints

- `GET /api/health`
- `POST /api/messages`
- `GET /api/topics`
- `GET /api/topics/{id}`
- `POST /api/query`
- `POST /api/reset-demo`

See `backend/API_CONTRACT.md` for request and response shapes.
