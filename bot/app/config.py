from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Settings(BaseSettings):
    """Configuração lida de variáveis de ambiente (ou de um arquivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    evolution_url: str = "http://localhost:8080"
    evolution_api_key: str
    webhook_token: str
    # Números que o bot responde, separados por vírgula (ex.: 5511999999999). Vazio = todos
    allowed_numbers: str = ""

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b-instruct"
    ollama_temperature: float = 0.3
    ollama_timeout_seconds: float = 120

    redis_url: str = "redis://localhost:6379/1"
    history_max_messages: int = 10
    history_ttl_seconds: int = 60 * 60 * 24

    system_prompt_path: Path = PROMPTS_DIR / "system_prompt.txt"
    fallback_reply: str = (
        "Desculpe, estou com uma instabilidade no momento. "
        "Um atendente vai falar com você em breve."
    )

    log_level: str = "INFO"

    def is_number_allowed(self, chat_id: str) -> bool:
        allowed = {number.strip() for number in self.allowed_numbers.split(",") if number.strip()}
        return not allowed or chat_id.split("@")[0] in allowed

    def load_system_prompt(self) -> str:
        return self.system_prompt_path.read_text(encoding="utf-8").strip()
