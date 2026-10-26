# Chatbot de atendimento no WhatsApp

Bot que responde clientes no WhatsApp usando IA local. A [Evolution API](https://doc.evolution-api.com) conecta o WhatsApp e o [Ollama](https://ollama.com) roda o modelo de linguagem na sua máquina, sem custo por mensagem.

```
Cliente ──► WhatsApp ──► Evolution API ──webhook──► bot (FastAPI) ──► Ollama
                              ▲                        │
                              └──── sendText ◄─────────┘   histórico no Redis
```

## Como rodar

Requisitos: Docker Desktop aberto.

```powershell
copy .env.example .env      # edite as chaves e senhas
docker compose up -d --build
```

Na primeira execução o modelo (~2,5 GB) é baixado; acompanhe com `docker compose logs -f ollama-pull`.

### Conectar o WhatsApp

1. Crie uma instância (troque `SUA_CHAVE` pelo `EVOLUTION_API_KEY` do `.env`):

   ```powershell
   curl.exe -X POST http://localhost:8080/instance/create `
     -H "apikey: SUA_CHAVE" -H "Content-Type: application/json" `
     -d '{\"instanceName\": \"atendimento\", \"integration\": \"WHATSAPP-BAILEYS\", \"qrcode\": true}'
   ```

2. Leia o QR Code com o WhatsApp do número da empresa. Ele vem na resposta acima, ou pode ser obtido pelo painel em http://localhost:8080/manager.
3. Mande uma mensagem de outro celular para esse número. O bot responde.

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
