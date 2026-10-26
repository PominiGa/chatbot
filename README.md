# Chatbot de atendimento no WhatsApp

Bot que responde clientes no WhatsApp usando IA local. A [Evolution API](https://doc.evolution-api.com) conecta o WhatsApp e o [Ollama](https://ollama.com) roda o modelo de linguagem na sua máquina, sem custo por mensagem.

```
Cliente ──► WhatsApp ──► Evolution API ──webhook──► bot (FastAPI) ──► Ollama
                              ▲                        │
                              └──── sendText ◄─────────┘   histórico no Redis
```

## Como rodar

Este compose sobe apenas o **Ollama** e o **bot**. A Evolution API, o Postgres e o Redis são os que já rodam no projeto Automacao, na rede Docker `venv_evolution-net`. Se eles mudarem, ajuste as variáveis comentadas no `.env.example`.

Requisitos: Docker Desktop aberto e a Evolution API do projeto Automacao rodando.

```powershell
copy .env.example .env      # preencha a chave da Evolution, o token e os números de teste
docker compose up -d --build
```

Na primeira execução o modelo (~2,5 GB) é baixado; acompanhe com `docker compose logs -f ollama-pull`.

### Apontar a Evolution para o bot

Configure o webhook da instância (troque `SUA_CHAVE`, `INSTANCIA` e `SEU_TOKEN`):

```powershell
curl.exe -X POST http://localhost:8081/webhook/set/INSTANCIA `
  -H "apikey: SUA_CHAVE" -H "Content-Type: application/json" `
  -d '{\"webhook\": {\"enabled\": true, \"url\": \"http://chatbot-bot-1:8000/webhook/SEU_TOKEN\", \"events\": [\"MESSAGES_UPSERT\"]}}'
```

### Testar com segurança

Preencha `ALLOWED_NUMBERS` no `.env` (ex.: `5511999999999,5511888888888`) para o bot responder **apenas** esses números. Os outros são ignorados e aparecem no log (`docker compose logs -f bot`). Deixe vazio para atender todos.

## Personalizar o atendimento

Edite [`bot/app/prompts/system_prompt.txt`](bot/app/prompts/system_prompt.txt) com as informações da sua empresa e rode `docker compose up -d --build bot`.

Outras opções (modelo, temperatura, tamanho do histórico, mensagem de erro) ficam em [`bot/app/config.py`](bot/app/config.py) e podem ser sobrescritas por variáveis de ambiente.

## Estrutura

```
bot/app/
├── main.py                  # monta a aplicação e injeta as dependências
├── config.py                # configurações via variáveis de ambiente
├── api/webhook.py           # rota que recebe os eventos da Evolution API
├── domain/                  # modelos e contratos (sem dependência de bibliotecas externas)
├── services/chat_service.py # regra do atendimento: histórico → IA → resposta
├── integrations/            # Evolution API, Ollama e Redis
└── prompts/                 # instruções da IA
```

O `ChatService` depende apenas dos contratos em `domain/ports.py`. Para trocar o Ollama por outra IA, ou o Redis por outro banco, basta criar uma nova classe em `integrations/` e ligá-la em `main.py`.

## Desenvolvimento

```powershell
cd bot
python -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```
