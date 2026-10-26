"""Tudo que é específico da Evolution API: formato do webhook e envio de mensagens."""

from typing import Any
from urllib.parse import quote

import httpx

from app.domain.models import IncomingMessage

MESSAGES_UPSERT_EVENT = "messages.upsert"
# Grupos, status e canais não são atendidos pelo bot
IGNORED_CHAT_SUFFIXES = ("@g.us", "@broadcast", "@newsletter")


def parse_incoming_message(payload: dict[str, Any]) -> IncomingMessage | None:
    """Converte o webhook em IncomingMessage, ou None se o evento não deve ser respondido."""
    if payload.get("event") != MESSAGES_UPSERT_EVENT:
        return None

    data = payload.get("data") or {}
    key = data.get("key") or {}
    chat_id = key.get("remoteJid") or ""
    if key.get("fromMe") or not chat_id or chat_id.endswith(IGNORED_CHAT_SUFFIXES):
        return None

    text = _extract_text(data.get("message") or {}).strip()
    if not text:
        return None

    return IncomingMessage(instance=payload.get("instance", ""), chat_id=chat_id, text=text)


def _extract_text(message: dict[str, Any]) -> str:
    extended = message.get("extendedTextMessage") or {}
    return message.get("conversation") or extended.get("text") or ""


class EvolutionClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def send_text(self, instance: str, chat_id: str, text: str) -> None:
        response = await self._http.post(
            f"/message/sendText/{quote(instance, safe='')}",
            json={"number": chat_id, "text": text},
        )
        response.raise_for_status()
