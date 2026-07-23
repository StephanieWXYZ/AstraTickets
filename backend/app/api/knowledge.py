from functools import lru_cache
from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.models import UserRole
from app.rag import KnowledgeBaseStore
from app.rag.embeddings import SentenceTransformerEmbedder
from app.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    KnowledgeMatch,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge base"])


@lru_cache
def get_knowledge_store() -> KnowledgeBaseStore:
    settings = get_settings()
    return KnowledgeBaseStore(
        path=settings.chroma_path,
        embedder=SentenceTransformerEmbedder(settings.embedding_model),
    )


KnowledgeStore = Annotated[KnowledgeBaseStore, Depends(get_knowledge_store)]


@router.post(
    "/documents",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def ingest_document(
    document: KnowledgeDocumentCreate,
    current_user: CurrentUser,
    store: KnowledgeStore,
) -> KnowledgeDocumentRead:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Administrator access required")
    source_id, chunks_added = store.ingest(
        text=document.text,
        title=document.title,
        source=document.source,
        source_id=document.source_id,
    )
    return KnowledgeDocumentRead(source_id=source_id, chunks_added=chunks_added)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    search: KnowledgeSearchRequest,
    current_user: CurrentUser,
    store: KnowledgeStore,
) -> KnowledgeSearchResponse:
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Staff access required")

    started = perf_counter()
    matches = store.search(search.query, search.limit)
    retrieval_ms = (perf_counter() - started) * 1000
    return KnowledgeSearchResponse(
        query=search.query,
        matches=[KnowledgeMatch.model_validate(match, from_attributes=True) for match in matches],
        retrieval_ms=round(retrieval_ms, 3),
    )
