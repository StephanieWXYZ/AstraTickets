from collections.abc import Sequence
from typing import Protocol

import httpx


class GenerationUnavailableError(RuntimeError):
    pass


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> str: ...


class OpenAICompatibleGenerator:
    def __init__(
        self,
        *,
        base_url: str | None,
        model: str | None,
        api_key: str | None,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def generate(self, prompt: str) -> str:
        if not self.base_url or not self.model:
            raise GenerationUnavailableError(
                "Answer generation is not configured on the server"
            )

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    "/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "temperature": 0.1,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You draft customer-support replies using only the supplied "
                                    "knowledge-base evidence."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise GenerationUnavailableError(
                "The configured answer-generation service is unavailable"
            ) from error

        try:
            choices: Sequence[object] = response.json()["choices"]
            message = choices[0]["message"]  # type: ignore[index]
            content = message["content"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise GenerationUnavailableError(
                "The answer-generation service returned an invalid response"
            ) from error
        if not isinstance(content, str) or not content.strip():
            raise GenerationUnavailableError(
                "The answer-generation service returned an empty response"
            )
        return content.strip()
