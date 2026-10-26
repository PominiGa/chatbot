from typing import Any

import pytest

from app.domain.models import IncomingMessage
from app.integrations.evolution import parse_incoming_message


def webhook(
    remote_jid: str = "5511999999999@s.whatsapp.net",
    message: dict[str, Any] | None = None,
    from_me: bool = False,
    event: str = "messages.upsert",
) -> dict[str, Any]:
    return {
        "event": event,
        "instance": "loja",
        "data": {
            "key": {"remoteJid": remote_jid, "fromMe": from_me, "id": "ABC"},
            "pushName": "Maria",
            "message": message if message is not None else {"conversation": " Oi "},
        },
    }


def test_parses_plain_text_message() -> None:
    assert parse_incoming_message(webhook()) == IncomingMessage(
        instance="loja", chat_id="5511999999999@s.whatsapp.net", text="Oi"
    )


def test_uses_phone_number_when_contact_comes_with_hidden_id() -> None:
    payload = webhook(remote_jid="123456789@lid")
    payload["data"]["key"]["remoteJidAlt"] = "5511999999999@s.whatsapp.net"

    parsed = parse_incoming_message(payload)

    assert parsed is not None
    assert parsed.chat_id == "5511999999999@s.whatsapp.net"


def test_parses_extended_text_message() -> None:
    payload = webhook(message={"extendedTextMessage": {"text": "Qual o horário?"}})

    parsed = parse_incoming_message(payload)

    assert parsed is not None
    assert parsed.text == "Qual o horário?"


@pytest.mark.parametrize(
    "payload",
    [
        webhook(event="connection.update"),
        webhook(from_me=True),
        webhook(remote_jid="123456@g.us"),
        webhook(remote_jid="status@broadcast"),
        webhook(message={"imageMessage": {"url": "..."}}),
        webhook(message={"conversation": "   "}),
        {},
    ],
    ids=["outro-evento", "enviada-por-mim", "grupo", "status", "sem-texto", "em-branco", "vazio"],
)
def test_ignores_messages_the_bot_should_not_answer(payload: dict[str, Any]) -> None:
    assert parse_incoming_message(payload) is None
