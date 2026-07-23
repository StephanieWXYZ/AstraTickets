from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated

DocumentText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=20)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class KnowledgeDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: DocumentText
    title: ShortText
    source: ShortText
    source_id: str | None = Field(default=None, min_length=1, max_length=100)


class KnowledgeDocumentRead(BaseModel):
    source_id: str
    chunks_added: int


class KnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=1000)]
    limit: int = Field(default=5, ge=1, le=10)


class KnowledgeMatch(BaseModel):
    chunk_id: str
    text: str
    source_id: str
    source: str
    title: str
    chunk_index: int
    score: float = Field(ge=0, le=1)


class KnowledgeSearchResponse(BaseModel):
    query: str
    matches: list[KnowledgeMatch]
    retrieval_ms: float = Field(ge=0)
