import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.ai import (
    GroundedAnswerService,
    GroundedDraft,
    GroundedSource,
    UngroundedAnswerError,
)
from app.ai.grounded_answers import REFUSAL_MESSAGE
from app.ai.generation import GenerationUnavailableError, OpenAICompatibleGenerator
from app.api.ai import get_grounded_answer_service
from app.main import app
from app.models import UserRole
from app.rag import SearchMatch
from tests.api_helpers import claim_ticket, create_staff_token, create_ticket, register_and_login


def knowledge_match(score: float = 0.91) -> SearchMatch:
    return SearchMatch(
        chunk_id="password-policy:0",
        text="Password reset links expire after 15 minutes.",
        source_id="password-policy",
        source="password-reset.md",
        title="Password Reset Policy",
        chunk_index=0,
        score=score,
    )


class FakeStore:
    def __init__(self, matches: list[SearchMatch]) -> None:
        self.matches = matches

    def search(self, _query: str, limit: int = 5) -> list[SearchMatch]:
        return self.matches[:limit]


class FakeGenerator:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer


class FakeDraftService:
    def __init__(self, draft: GroundedDraft) -> None:
        self.draft_result = draft
        self.questions: list[str] = []

    def draft(self, question: str, _limit: int = 4) -> GroundedDraft:
        self.questions.append(question)
        return self.draft_result


def test_grounded_service_returns_only_cited_sources() -> None:
    generator = FakeGenerator("Reset links expire after 15 minutes [1].")
    service = GroundedAnswerService(FakeStore([knowledge_match()]), generator)

    draft = service.draft("When does my reset link expire?")

    assert draft.status == "answered"
    assert draft.sources[0].reference == 1
    assert draft.sources[0].source == "password-reset.md"
    assert "Use only the numbered evidence" in generator.prompts[0]


def test_openai_compatible_generator_reads_chat_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer server-secret"
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Grounded answer [1]."}}]},
        )

    generator = OpenAICompatibleGenerator(
        base_url="https://models.example.com",
        model="support-model",
        api_key="server-secret",
        timeout_seconds=10,
        transport=httpx.MockTransport(handler),
    )

    assert generator.generate("Use evidence [1].") == "Grounded answer [1]."


def test_openai_compatible_generator_rejects_invalid_provider_response() -> None:
    generator = OpenAICompatibleGenerator(
        base_url="https://models.example.com",
        model="support-model",
        api_key=None,
        timeout_seconds=10,
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"choices": []})
        ),
    )

    with pytest.raises(GenerationUnavailableError, match="invalid response"):
        generator.generate("Use evidence [1].")


def test_grounded_service_refuses_weak_evidence_without_calling_model() -> None:
    generator = FakeGenerator("This answer must never be used.")
    service = GroundedAnswerService(
        FakeStore([knowledge_match(score=0.2)]),
        generator,
        min_score=0.4,
    )

    draft = service.draft("What is the cancellation fee?")

    assert draft.status == "insufficient_context"
    assert draft.answer == REFUSAL_MESSAGE
    assert draft.sources == []
    assert generator.prompts == []


def test_grounded_service_rejects_uncited_model_output() -> None:
    service = GroundedAnswerService(
        FakeStore([knowledge_match()]),
        FakeGenerator("Reset links expire after 15 minutes."),
    )

    try:
        service.draft("When does my reset link expire?")
    except UngroundedAnswerError as error:
        assert "did not cite" in str(error)
    else:
        raise AssertionError("Uncited model output was accepted")


def test_grounded_service_rejects_invented_citation() -> None:
    service = GroundedAnswerService(
        FakeStore([knowledge_match()]),
        FakeGenerator("Reset links expire after 15 minutes [2]."),
    )

    try:
        service.draft("When does my reset link expire?")
    except UngroundedAnswerError as error:
        assert "unavailable" in str(error)
    else:
        raise AssertionError("Invented source citation was accepted")


def test_assigned_agent_can_request_grounded_draft(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Expired password reset link")
    agent_token = create_staff_token(session_factory)
    claim_ticket(client, agent_token, ticket["id"])
    source = GroundedSource(
        reference=1,
        chunk_id="password-policy:0",
        text="Password reset links expire after 15 minutes.",
        source_id="password-policy",
        source="password-reset.md",
        title="Password Reset Policy",
        chunk_index=0,
        score=0.91,
    )
    service = FakeDraftService(
        GroundedDraft(
            status="answered",
            answer="Request a new password reset link [1].",
            sources=[source],
            retrieval_ms=1.3,
        )
    )
    app.dependency_overrides[get_grounded_answer_service] = lambda: service
    try:
        response = client.post(
            f"/api/tickets/{ticket['id']}/ai-draft",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={},
        )
    finally:
        app.dependency_overrides.pop(get_grounded_answer_service, None)

    assert response.status_code == 200
    data = response.json()
    assert data["draft_only"] is True
    assert data["sources"][0]["title"] == "Password Reset Policy"
    assert data["retrieval_ms"] == 1.3
    assert "Expired password reset link" in service.questions[0]


def test_unassigned_agent_cannot_request_ai_draft(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Unassigned support request")
    agent_token = create_staff_token(session_factory)
    service = FakeDraftService(
        GroundedDraft("insufficient_context", REFUSAL_MESSAGE, [], 0.1)
    )
    app.dependency_overrides[get_grounded_answer_service] = lambda: service
    try:
        response = client.post(
            f"/api/tickets/{ticket['id']}/ai-draft",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={},
        )
    finally:
        app.dependency_overrides.pop(get_grounded_answer_service, None)

    assert response.status_code == 403
    assert service.questions == []


def test_customer_cannot_request_ai_draft(
    client: TestClient,
) -> None:
    token = register_and_login(client)
    ticket = create_ticket(client, token, "Customer-owned support request")
    service = FakeDraftService(
        GroundedDraft("insufficient_context", REFUSAL_MESSAGE, [], 0.1)
    )
    app.dependency_overrides[get_grounded_answer_service] = lambda: service
    try:
        response = client.post(
            f"/api/tickets/{ticket['id']}/ai-draft",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
    finally:
        app.dependency_overrides.pop(get_grounded_answer_service, None)

    assert response.status_code == 403
    assert service.questions == []
