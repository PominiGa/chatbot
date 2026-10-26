from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.webhook import get_chat_service, get_settings
from app.config import Settings
from app.main import create_app
from app.services.chat_service import ChatService
from tests.fakes import FakeLanguageModel, FakeSender, InMemoryHistory

PAYLOAD = {
    "event": "messages.upsert",
    "instance": "loja",
    "data": {
        "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
        "message": {"conversation": "Oi"},
    },
}


@pytest.fixture
def sender() -> FakeSender:
    return FakeSender()


@pytest.fixture
def settings() -> Settings:
    return Settings(evolution_api_key="chave", webhook_token="segredo")


@pytest.fixture
def client(sender: FakeSender, settings: Settings) -> Iterator[TestClient]:
    app = create_app()
    service = ChatService(
        FakeLanguageModel(answer="Olá!"), sender, InMemoryHistory(), "prompt", "erro"
    )
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_chat_service] = lambda: service
    # Sem "with": o lifespan não roda, então nada se conecta a serviços externos
    yield TestClient(app)


def test_answers_customer_message(client: TestClient, sender: FakeSender) -> None:
    response = client.post("/webhook/segredo", json=PAYLOAD)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    assert sender.sent == [("loja", "5511999999999@s.whatsapp.net", "Olá!")]


def test_rejects_wrong_token(client: TestClient, sender: FakeSender) -> None:
    response = client.post("/webhook/errado", json=PAYLOAD)

    assert response.status_code == 404
    assert sender.sent == []


def test_ignores_irrelevant_events(client: TestClient, sender: FakeSender) -> None:
    response = client.post("/webhook/segredo", json={"event": "connection.update"})

    assert response.json() == {"status": "ignored"}
    assert sender.sent == []


def test_answers_only_allowed_numbers(
    client: TestClient, sender: FakeSender, settings: Settings
) -> None:
    settings.allowed_numbers = "5511888888888, 5511999999999"
    client.post("/webhook/segredo", json=PAYLOAD)

    settings.allowed_numbers = "5511888888888"
    response = client.post("/webhook/segredo", json=PAYLOAD)

    assert response.json() == {"status": "ignored"}
    assert sender.sent == [("loja", "5511999999999@s.whatsapp.net", "Olá!")]


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
