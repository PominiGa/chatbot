from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class IncomingMessage:
    """Mensagem de texto enviada por um cliente."""

    instance: str
    chat_id: str
    text: str

    @property
    def conversation_id(self) -> str:
        # O mesmo cliente pode falar com mais de um número (instância) da empresa
        return f"{self.instance}:{self.chat_id}"
