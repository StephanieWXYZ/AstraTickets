from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class AIDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=5000),
    ] | None = None
    limit: int = Field(default=4, ge=1, le=8)


class AISource(BaseModel):
    reference: int = Field(ge=1)
    chunk_id: str
    text: str
    source_id: str
    source: str
    title: str
    chunk_index: int = Field(ge=0)
    score: float = Field(ge=0, le=1)


class AIDraftResponse(BaseModel):
    ticket_id: int
    status: Literal["answered", "insufficient_context"]
    answer: str
    sources: list[AISource]
    retrieval_ms: float = Field(ge=0)
    draft_only: Literal[True] = True
