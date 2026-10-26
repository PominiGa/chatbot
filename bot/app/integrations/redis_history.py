import json
from dataclasses import asdict

from redis.asyncio import Redis

from app.domain.models import ChatMessage


class RedisConversationHistory:
    """Guarda as últimas mensagens de cada conversa, que expiram após um período sem contato."""

    def __init__(self, redis: Redis, max_messages: int, ttl_seconds: int) -> None:
        self._redis = redis
        self._max_messages = max_messages
        self._ttl_seconds = ttl_seconds

    async def get(self, conversation_id: str) -> list[ChatMessage]:
        items = await self._redis.lrange(self._key(conversation_id), 0, -1)
        return [ChatMessage(**json.loads(item)) for item in items]

    async def append(self, conversation_id: str, *messages: ChatMessage) -> None:
        key = self._key(conversation_id)
        serialized = [json.dumps(asdict(message), ensure_ascii=False) for message in messages]
        async with self._redis.pipeline(transaction=True) as pipe:
            await (
                pipe.rpush(key, *serialized)
                .ltrim(key, -self._max_messages, -1)
                .expire(key, self._ttl_seconds)
                .execute()
            )

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"chatbot:history:{conversation_id}"
