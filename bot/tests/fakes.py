from collections import defaultdict
from collections.abc import Sequence

from app.domain.models import ChatMessage
from app.domain.ports import LanguageModelError


class FakeLanguageModel:
    def __init__(self, answer: str = "Olá! Como posso ajudar?", fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.received: list[ChatMessage] = []

    async def reply(self, messages: Sequence[ChatMessage]) -> str:
        self.received = list(messages)
        if self.fail:
            raise LanguageModelError("falha simulada")
        return self.answer


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send_text(self, instance: str, chat_id: str, text: str) -> None:
        self.sent.append((instance, chat_id, text))


class InMemoryHistory:
    def __init__(self) -> None:
        self.conversations: dict[str, list[ChatMessage]] = defaultdict(list)

    async def get(self, conversation_id: str) -> list[ChatMessage]:
        return list(self.conversations[conversation_id])

    async def append(self, conversation_id: str, *messages: ChatMessage) -> None:
        self.conversations[conversation_id].extend(messages)
