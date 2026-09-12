from fastapi import APIRouter, Depends, HTTPException

from backend.app.dependencies import get_memory_engine
from backend.app.models import (
    MessageIngestRequest,
    MessageIngestResponse,
    QueryRequest,
    QueryResponse,
    ResetDemoResponse,
    TopicDetailResponse,
    TopicsResponse,
)
from backend.app.service import MemoryEngine

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/messages", response_model=MessageIngestResponse)
def ingest_message(
    payload: MessageIngestRequest,
    engine: MemoryEngine = Depends(get_memory_engine),
) -> MessageIngestResponse:
    try:
        return engine.ingest_message(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": str(exc)}) from exc


@router.get("/topics", response_model=TopicsResponse)
def list_topics(
    workspaceId: str = "demo",
    engine: MemoryEngine = Depends(get_memory_engine),
) -> TopicsResponse:
    return engine.list_topics(workspaceId)


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse)
def get_topic(
    topic_id: str,
    workspaceId: str = "demo",
    engine: MemoryEngine = Depends(get_memory_engine),
) -> TopicDetailResponse:
    topic = engine.get_topic(workspaceId, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Topic not found"})
    return topic


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    engine: MemoryEngine = Depends(get_memory_engine),
) -> QueryResponse:
    return engine.query(payload)


@router.post("/reset-demo", response_model=ResetDemoResponse)
def reset_demo(engine: MemoryEngine = Depends(get_memory_engine)) -> ResetDemoResponse:
    return engine.reset_demo()
