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
uvicorn backend.app.main:app --reload
```

## Test

```bash
python -m pytest backend_tests
```

## Endpoints

- `GET /api/health`
- `POST /api/messages`
- `GET /api/topics`
- `GET /api/topics/{id}`
- `POST /api/query`
- `POST /api/reset-demo`

See `backend/API_CONTRACT.md` for request and response shapes.
