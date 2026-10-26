import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.webhook import router
from app.config import Settings
from app.integrations.evolution import EvolutionClient
from app.integrations.ollama import OllamaChatModel
from app.integrations.redis_history import RedisConversationHistory
from app.services.chat_service import ChatService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Cria as dependências na subida da aplicação e as fecha no desligamento."""
    settings = Settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    async with (
        httpx.AsyncClient(
            base_url=settings.ollama_url, timeout=settings.ollama_timeout_seconds
        ) as ollama_http,
        httpx.AsyncClient(
            base_url=settings.evolution_url,
            headers={"apikey": settings.evolution_api_key},
            timeout=30,
        ) as evolution_http,
    ):
        app.state.settings = settings
        app.state.chat_service = ChatService(
            llm=OllamaChatModel(ollama_http, settings.ollama_model, settings.ollama_temperature),
            sender=EvolutionClient(evolution_http),
            history=RedisConversationHistory(
                redis, settings.history_max_messages, settings.history_ttl_seconds
            ),
            system_prompt=settings.load_system_prompt(),
            fallback_reply=settings.fallback_reply,
        )
        yield
    await redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="Chatbot de atendimento", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
