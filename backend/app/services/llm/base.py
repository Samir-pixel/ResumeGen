"""LLM Provider abstraction — все сервисы используют этот интерфейс."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """Протокол для LLM-провайдеров."""

    async def generate(self, system: str, user: str, response_model: type[T]) -> T: ...


# ── Конфигурация провайдеров ──────────────────────────────────────────────────
# base_url и рекомендуемая модель для каждого провайдера

_PROVIDER_CONFIGS: dict[str, dict] = {
    # ── OpenAI (платный, лучшее качество) ────────────────────────────────────
    "openai": {
        "base_url": "",
        "default_model": "gpt-4o-mini",   # качество + скорость + цена
        "quality_model": "gpt-4o",        # для максимального качества
        "is_local": False,
    },

    # ── Google Gemini ─────────────────────────────────────────────────────────
    # БЕСПЛАТНО | РЕКОМЕНДУЕТСЯ для качества
    # Ключ: https://aistudio.google.com/app/apikey
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        # gemini-3.5-flash-lite: высокий бесплатный лимит + хорошее качество
        # gemini-flash-lite-latest: всегда указывает на последнюю lite-версию
        "default_model": "gemini-3.5-flash-lite",
        "quality_model": "gemini-flash-latest",   # если нужно ещё лучше (меньше лимит)
        "is_local": False,
    },

    # ── Groq ──────────────────────────────────────────────────────────────────
    # БЕСПЛАТНО | 14 400 req/day
    # Ключ: https://console.groq.com
    # Для КАЧЕСТВА используй 70B модель, для скорости — 8B
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",   # 70B — высокое качество
        "quality_model": "llama-3.3-70b-versatile",
        "is_local": False,
    },

    # ── Ollama (локально) ─────────────────────────────────────────────────────
    # БЕСПЛАТНО | Офлайн | 8GB RAM для 7B, 16GB для 14B
    # Установка: https://ollama.com → ollama pull qwen2.5:14b
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:14b",    # качество — нужно 10GB RAM
        "quality_model": "qwen2.5:32b",    # максимум — нужно 20GB RAM
        "is_local": True,
    },

    # ── Kimi (Moonshot AI) ────────────────────────────────────────────────────
    # БЕСПЛАТНО | 15M токенов/месяц
    # Ключ: https://platform.moonshot.cn
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-32k",   # 32k контекст — лучшее качество
        "quality_model": "moonshot-v1-128k",
        "is_local": False,
    },

    # ── OpenRouter ────────────────────────────────────────────────────────────
    # Агрегатор, есть бесплатные модели
    # Ключ: https://openrouter.ai/keys
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-2.0-flash-exp:free",  # бесплатно + качество
        "quality_model": "anthropic/claude-3-5-haiku",        # платно но дёшево
        "is_local": False,
    },
}


def create_provider(settings: "Settings") -> "LLMProvider | None":
    """Фабрика провайдеров.

    Создаёт провайдер на основе LLM_PROVIDER из настроек.
    Если ключ не задан (или провайдер=heuristic) — возвращает None.
    Все провайдеры используют единый OpenAI-совместимый интерфейс.
    """
    from app.services.llm.openai_provider import OpenAIProvider

    provider_name = settings.llm_provider.lower().strip()

    if provider_name == "heuristic":
        logger.info("LLM провайдер: эвристика (heuristic)")
        return None

    cfg = _PROVIDER_CONFIGS.get(provider_name)
    if cfg is None:
        logger.warning(
            "Неизвестный LLM_PROVIDER='%s'. Доступные: %s. Используем эвристику.",
            provider_name,
            ", ".join(_PROVIDER_CONFIGS.keys()),
        )
        return None

    # Для всех провайдеров кроме ollama требуем API ключ
    is_local = cfg["is_local"]
    if not is_local and not settings.llm_api_key:
        logger.warning(
            "LLM_PROVIDER=%s требует LLM_API_KEY — используем эвристику. "
            "Получите бесплатный ключ:\n"
            "  gemini:     https://aistudio.google.com/app/apikey\n"
            "  groq:       https://console.groq.com\n"
            "  kimi:       https://platform.moonshot.cn\n"
            "  openrouter: https://openrouter.ai/keys",
            provider_name,
        )
        return None

    # Определяем base_url: приоритет у LLM_BASE_URL из .env
    base_url = settings.llm_base_url.strip() or cfg["base_url"]

    # Определяем модель:
    # - если пользователь явно задал LLM_MODEL в .env → используем его
    # - если LLM_MODEL = дефолт OpenAI (gpt-4o-mini) и провайдер не OpenAI → берём дефолт провайдера
    model = settings.llm_model
    if model in ("gpt-4o-mini", "") and provider_name not in ("openai",):
        model = cfg["default_model"]

    api_key = settings.llm_api_key or "ollama"  # ollama принимает любой ключ

    logger.info(
        "LLM провайдер: %s | модель: %s | base_url: %s",
        provider_name,
        model,
        base_url or "default",
    )

    return OpenAIProvider(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=settings.llm_timeout,
        is_local=is_local,
        provider_name=provider_name,
    )
