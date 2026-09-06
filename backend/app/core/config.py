from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта — две папки вверх от этого файла (backend/app/core/config.py → project root)
_HERE = Path(__file__).resolve().parent          # app/core/
_BACKEND = _HERE.parent.parent                    # backend/
_PROJECT_ROOT = _BACKEND.parent                   # project root

# Путь к шаблонам (templates/ в корне проекта)
_DEFAULT_TEMPLATES = _PROJECT_ROOT / "templates"
_DEFAULT_PROMPTS_ROOT = _PROJECT_ROOT / "prompts"
_DEFAULT_STORAGE = _BACKEND / "storage"


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./resume_generator.db"
    redis_url: str = "redis://localhost:6379/0"

    # LLM ─────────────────────────────────────────────────────────────────────
    # LLM_PROVIDER варианты:
    #   "heuristic"  — без LLM, быстро, качество ниже
    #   "openai"     — OpenAI API (требует LLM_API_KEY + оплаты)
    #   "gemini"     — Google Gemini Flash (бесплатно, 1M req/day)
    #   "groq"       — Groq Cloud (бесплатно, ультра-быстрый)
    #   "ollama"     — Локальная модель через Ollama (бесплатно, офлайн)
    #   "kimi"       — Moonshot AI / Kimi (бесплатно, 15M tok/мес)
    #   "openrouter" — OpenRouter (агрегатор, есть бесплатные модели)
    llm_provider: str = "heuristic"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    # Base URL — если пусто, используется дефолт провайдера
    # Ollama: http://localhost:11434/v1
    # LM Studio: http://localhost:1234/v1
    llm_base_url: str = ""
    # Таймаут запроса в секундах (локальные модели медленнее, особенно на CPU)
    llm_timeout: int = 180

    # Storage (переопределяется через env в Docker)
    storage_dir: Path = _DEFAULT_STORAGE
    pdf_storage_dir: Path = _DEFAULT_STORAGE / "pdfs"
    generated_storage_dir: Path = _DEFAULT_STORAGE / "generated"
    templates_dir: Path = _DEFAULT_TEMPLATES
    prompts_dir: Path = _DEFAULT_PROMPTS_ROOT
    prompt_version: str = "v1"

    frontend_url: str = "http://localhost:3000"
    cors_origins: str = ""

    # Pipeline
    critic_threshold: int = 70        # ниже порога — доработка или перегенерация
    max_critic_iterations: int = 4    # максимум циклов оценка → правка
    max_consistency_retries: int = 2  # максимум попыток исправить карьеру

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_storage(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
        self.generated_storage_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_storage()
    return settings
