from collections.abc import Sequence
from dataclasses import asdict

import httpx

from app.domain.models import ChatMessage
from app.domain.ports import LanguageModelError


class OllamaChatModel:
    def __init__(self, http: httpx.AsyncClient, model: str, temperature: float) -> None:
        self._http = http
        self._model = model
        self._temperature = temperature

    async def reply(self, messages: Sequence[ChatMessage]) -> str:
        payload = {
            "model": self._model,
            "messages": [asdict(message) for message in messages],
            "stream": False,
            "think": False,  # sem "modo pensamento": respostas bem mais rápidas
            "options": {"temperature": self._temperature},
        }
        try:
            response = await self._http.post("/api/chat", json=payload)
            response.raise_for_status()
            content = response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise LanguageModelError(f"Ollama falhou: {error}") from error

        answer = content.strip()
        if not answer:
            raise LanguageModelError("Ollama retornou uma resposta vazia")
        return answer
