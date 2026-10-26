from app.domain.models import ChatMessage, IncomingMessage
from app.services.chat_service import ChatService
from tests.fakes import FakeLanguageModel, FakeSender, InMemoryHistory

MESSAGE = IncomingMessage(instance="loja", chat_id="5511999999999@s.whatsapp.net", text="Oi")


def make_service(llm: FakeLanguageModel) -> tuple[ChatService, FakeSender, InMemoryHistory]:
    sender, history = FakeSender(), InMemoryHistory()
    service = ChatService(llm, sender, history, system_prompt="Seja gentil", fallback_reply="Erro")
    return service, sender, history


async def test_sends_model_answer_to_customer() -> None:
    service, sender, _ = make_service(FakeLanguageModel(answer="Olá!"))

    await service.handle(MESSAGE)

    assert sender.sent == [("loja", MESSAGE.chat_id, "Olá!")]


async def test_prompt_contains_system_prompt_history_and_new_message() -> None:
    llm = FakeLanguageModel()
    service, _, history = make_service(llm)
    earlier = [ChatMessage("user", "Bom dia"), ChatMessage("assistant", "Bom dia!")]
    await history.append(MESSAGE.conversation_id, *earlier)

    await service.handle(MESSAGE)

    assert llm.received == [
        ChatMessage("system", "Seja gentil"),
        *earlier,
        ChatMessage("user", "Oi"),
    ]


async def test_saves_exchange_in_history() -> None:
    service, _, history = make_service(FakeLanguageModel(answer="Olá!"))

    await service.handle(MESSAGE)

    assert history.conversations[MESSAGE.conversation_id] == [
        ChatMessage("user", "Oi"),
        ChatMessage("assistant", "Olá!"),
    ]


async def test_sends_fallback_and_skips_history_when_model_fails() -> None:
    service, sender, history = make_service(FakeLanguageModel(fail=True))

    await service.handle(MESSAGE)

    assert sender.sent == [("loja", MESSAGE.chat_id, "Erro")]
    assert history.conversations[MESSAGE.conversation_id] == []
