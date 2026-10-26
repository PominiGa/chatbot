import logging

from app.domain.models import ChatMessage, IncomingMessage
from app.domain.ports import (
    ConversationHistory,
    LanguageModel,
    LanguageModelError,
    MessageSender,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Recebe a mensagem do cliente, gera a resposta com a IA e envia de volta."""

    def __init__(
        self,
        llm: LanguageModel,
        sender: MessageSender,
        history: ConversationHistory,
        system_prompt: str,
        fallback_reply: str,
    ) -> None:
        self._llm = llm
        self._sender = sender
        self._history = history
        self._system_prompt = system_prompt
        self._fallback_reply = fallback_reply

    async def handle(self, message: IncomingMessage) -> None:
        user_message = ChatMessage(role="user", content=message.text)
        past_messages = await self._history.get(message.conversation_id)
        prompt = [
            ChatMessage(role="system", content=self._system_prompt),
            *past_messages,
            user_message,
        ]

        try:
            answer = await self._llm.reply(prompt)
        except LanguageModelError:
            logger.exception("Falha ao gerar resposta para %s", message.conversation_id)
            await self._sender.send_text(message.instance, message.chat_id, self._fallback_reply)
            return

        await self._history.append(
            message.conversation_id,
            user_message,
            ChatMessage(role="assistant", content=answer),
        )
        await self._sender.send_text(message.instance, message.chat_id, answer)
