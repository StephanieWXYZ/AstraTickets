from collections.abc import Sequence
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.api.knowledge import get_knowledge_store
from app.main import app
from app.models import UserRole
from app.rag import KnowledgeBaseStore, SearchMatch
from app.rag.chunking import chunk_document
from tests.api_helpers import create_staff_token, register_and_login


class KeywordEmbedder:
    vocabulary = ("password", "refund", "account")

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float(text.lower().count(word)) for word in self.vocabulary]
            for text in texts
        ]


class FakeKnowledgeStore:
    def __init__(self) -> None:
        self.ingested: list[dict[str, str | None]] = []

    def ingest(
        self,
        *,
        text: str,
        title: str,
        source: str,
        source_id: str | None = None,
    ) -> tuple[str, int]:
        self.ingested.append(
            {"text": text, "title": title, "source": source, "source_id": source_id}
        )
        return source_id or "generated-source", 2

    def search(self, query: str, limit: int = 5) -> list[SearchMatch]:
        return [
            SearchMatch(
                chunk_id="password-policy:0",
                text="Password reset links expire after 15 minutes.",
                source_id="password-policy",
                source="password-reset.md",
                title="Password Reset Policy",
                chunk_index=0,
                score=0.91,
            )
        ][:limit]


def test_chunk_document_preserves_content_with_bounded_chunks() -> None:
    text = "First policy paragraph. " * 20 + "\n\n" + "Second policy paragraph. " * 20

    chunks = chunk_document(text, max_chars=180, overlap_chars=20)

    assert len(chunks) > 2
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 180 for chunk in chunks)
    assert "First policy paragraph." in chunks[0]


def test_chunk_document_safely_splits_very_long_tokens() -> None:
    chunks = chunk_document("x" * 450, max_chars=100, overlap_chars=0)

    assert len(chunks) == 5
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chroma_store_retrieves_source_metadata(tmp_path: Path) -> None:
    store = KnowledgeBaseStore(tmp_path / "chroma", KeywordEmbedder())
    store.ingest(
        text="Password reset links expire after 15 minutes. Contact support for account recovery.",
        title="Password Reset",
        source="password-reset.md",
        source_id="password-reset",
    )
    store.ingest(
        text="Refund requests are reviewed within five business days. Keep the payment receipt.",
        title="Refund Policy",
        source="refund-policy.md",
        source_id="refund-policy",
    )

    matches = store.search("My password reset is not working", limit=1)

    assert len(matches) == 1
    assert matches[0].source_id == "password-reset"
    assert matches[0].source == "password-reset.md"
    assert matches[0].title == "Password Reset"
    assert matches[0].score > 0


def test_admin_can_ingest_document(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    store = FakeKnowledgeStore()
    app.dependency_overrides[get_knowledge_store] = lambda: store
    token = create_staff_token(session_factory, UserRole.ADMIN)
    try:
        response = client.post(
            "/api/knowledge/documents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "text": "Password reset links expire after fifteen minutes.",
                "title": "Password Reset Policy",
                "source": "password-reset.md",
                "source_id": "password-policy",
            },
        )
    finally:
        app.dependency_overrides.pop(get_knowledge_store, None)

    assert response.status_code == 201
    assert response.json() == {"source_id": "password-policy", "chunks_added": 2}
    assert store.ingested[0]["title"] == "Password Reset Policy"


def test_non_admin_cannot_ingest_document(
    client: TestClient,
) -> None:
    token = register_and_login(client)
    response = client.post(
        "/api/knowledge/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Customers should not be able to change knowledge documents.",
            "title": "Restricted Document",
            "source": "restricted.md",
        },
    )

    assert response.status_code == 403


def test_staff_search_returns_structured_sources(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    store = FakeKnowledgeStore()
    app.dependency_overrides[get_knowledge_store] = lambda: store
    token = create_staff_token(session_factory, UserRole.AGENT)
    try:
        response = client.post(
            "/api/knowledge/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "When does a reset link expire?", "limit": 3},
        )
    finally:
        app.dependency_overrides.pop(get_knowledge_store, None)

    assert response.status_code == 200
    data = response.json()
    assert data["matches"][0]["source"] == "password-reset.md"
    assert data["matches"][0]["title"] == "Password Reset Policy"
    assert data["matches"][0]["chunk_index"] == 0
    assert data["retrieval_ms"] >= 0


def test_customer_cannot_search_internal_knowledge(client: TestClient) -> None:
    token = register_and_login(client)
    response = client.post(
        "/api/knowledge/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Show me internal support policies"},
    )

    assert response.status_code == 403
