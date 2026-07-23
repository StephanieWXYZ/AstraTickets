from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai import GroundedAnswerService, UngroundedAnswerError
from app.ai.generation import GenerationUnavailableError, OpenAICompatibleGenerator
from app.api.dependencies import CurrentUser
from app.api.knowledge import get_knowledge_store
from app.api.tickets import get_visible_ticket
from app.core.config import get_settings
from app.db.session import get_db
from app.models import TicketStatus, UserRole
from app.rag import KnowledgeBaseStore
from app.schemas import AIDraftRequest, AIDraftResponse, AISource

router = APIRouter(prefix="/tickets", tags=["AI assistance"])


def get_grounded_answer_service(
    store: Annotated[KnowledgeBaseStore, Depends(get_knowledge_store)],
) -> GroundedAnswerService:
    settings = get_settings()
    generator = OpenAICompatibleGenerator(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    return GroundedAnswerService(
        store=store,
        generator=generator,
        min_score=settings.knowledge_min_score,
    )


GroundedService = Annotated[GroundedAnswerService, Depends(get_grounded_answer_service)]


@router.post("/{ticket_id}/ai-draft", response_model=AIDraftResponse)
def draft_ticket_reply(
    ticket_id: int,
    request: AIDraftRequest,
    current_user: CurrentUser,
    service: GroundedService,
    session: Annotated[Session, Depends(get_db)],
) -> AIDraftResponse:
    ticket = get_visible_ticket(ticket_id, current_user, session)
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Staff access required")
    if current_user.role == UserRole.AGENT and ticket.assignee_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Agents can draft replies only for tickets assigned to them",
        )
    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed tickets must be reopened before drafting a reply",
        )

    question = request.question or f"{ticket.title}\n\n{ticket.description}"
    try:
        draft = service.draft(question, request.limit)
    except GenerationUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except UngroundedAnswerError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return AIDraftResponse(
        ticket_id=ticket.id,
        status=draft.status,
        answer=draft.answer,
        sources=[AISource.model_validate(source, from_attributes=True) for source in draft.sources],
        retrieval_ms=draft.retrieval_ms,
    )
