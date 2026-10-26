"""Contratos que o serviço de chat usa; as implementações concretas ficam em app.integrations."""

from collections.abc import Sequence
from typing import Protocol

from app.domain.models import ChatMessage


class LanguageModelError(Exception):
    """O modelo de linguagem não conseguiu gerar uma resposta."""


class LanguageModel(Protocol):
    async def reply(self, messages: Sequence[ChatMessage]) -> str: ...


class MessageSender(Protocol):
    async def send_text(self, instance: str, chat_id: str, text: str) -> None: ...


class ConversationHistory(Protocol):
    async def get(self, conversation_id: str) -> list[ChatMessage]: ...

    async def append(self, conversation_id: str, *messages: ChatMessage) -> None: ...
