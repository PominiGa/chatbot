import logging
import secrets
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.config import Settings
from app.integrations.evolution import parse_incoming_message
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/webhook/{token}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    token: str,
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> dict[str, str]:
    if not secrets.compare_digest(token, settings.webhook_token):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    message = parse_incoming_message(payload)
    if message is None:
        return {"status": "ignored"}
    if not settings.is_number_allowed(message.chat_id):
        logger.info("Ignorando %s: fora de ALLOWED_NUMBERS", message.chat_id)
        return {"status": "ignored"}

    # A IA leva alguns segundos; respondemos o webhook na hora e processamos em segundo plano
    background_tasks.add_task(chat_service.handle, message)
    return {"status": "accepted"}
