"""OpenAI-совместимый LLM провайдер.

Работает с любым OpenAI-compatible endpoint:
  - OpenAI (api.openai.com)
  - Google Gemini (generativelanguage.googleapis.com/v1beta/openai/)
  - Groq (api.groq.com/openai/v1)
  - Ollama (localhost:11434/v1)
  - Kimi / Moonshot (api.moonshot.cn/v1)
  - OpenRouter (openrouter.ai/api/v1)
  - LM Studio, Jan.ai и любой OpenAI-compatible сервер
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TypeVar

from openai import AsyncOpenAI, APIConnectionError, APIStatusError, InternalServerError, RateLimitError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Ошибки при которых нужно повторить запрос
_RETRYABLE = (RateLimitError, APIConnectionError, asyncio.TimeoutError, InternalServerError)

# Провайдеры у которых есть особенности работы с JSON mode
_GEMINI_PROVIDERS = {"gemini"}
# Провайдеры без поддержки json_object (используем prompt-only подход)
_NO_JSON_MODE = {"kimi", "openrouter"}


class OpenAIProvider:
    """Универсальный LLM провайдер на базе OpenAI-совместимого API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "",
        timeout: int = 180,
        is_local: bool = False,
        provider_name: str = "openai",
    ) -> None:
        client_kwargs: dict = {
            "api_key": api_key,
            "timeout": float(timeout),
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)
        self.model = model
        self.is_local = is_local
        self.provider_name = provider_name

        # Определяем режим генерации JSON
        self.use_json_mode = provider_name not in _NO_JSON_MODE
        self.is_gemini = provider_name in _GEMINI_PROVIDERS

        logger.info(
            "OpenAIProvider init: provider=%s model=%s url=%s json_mode=%s local=%s",
            provider_name, model, base_url or "default",
            self.use_json_mode, is_local,
        )

    async def generate(self, system: str, user: str, response_model: type[T]) -> T:
        schema = json.dumps(
            response_model.model_json_schema(), ensure_ascii=False, indent=2
        )

        # Системный промпт с инструкцией по JSON
        json_block = (
            "═══════════════════════════════════════════\n"
            "MANDATORY OUTPUT FORMAT:\n"
            "• Return ONLY a single valid JSON object.\n"
            "• No markdown code blocks, no explanation, no preamble.\n"
            "• The JSON must match this schema exactly:\n\n"
            f"{schema}\n"
            "═══════════════════════════════════════════"
        )
        full_system = f"{system}\n\n{json_block}"

        # Количество попыток: локальные нестабильны по JSON, облако — по доступности
        max_attempts = 4 if self.is_local else 5
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                response = await self._call(full_system, user)
                raw = response.choices[0].message.content or ""
                raw = _extract_json(raw)

                try:
                    return response_model.model_validate_json(raw)
                except (ValidationError, ValueError) as parse_exc:
                    logger.warning(
                        "[%s] Attempt %d: invalid JSON (%s). Preview: %.150s",
                        self.provider_name, attempt + 1, parse_exc, raw,
                    )
                    last_exc = parse_exc
                    # На второй попытке усиливаем инструкцию
                    if attempt == 1:
                        user = (
                            f"{user}\n\n"
                            "⚠️ IMPORTANT: Your last response was not valid JSON. "
                            "Return ONLY the JSON object. Start your response with {{ and end with }}."
                        )
                    await asyncio.sleep(1.5)

            except _RETRYABLE as exc:
                exc_str = str(exc)
                # Пытаемся извлечь retryDelay из ответа API (секунды)
                retry_delay = _parse_retry_delay(exc_str)
                if retry_delay:
                    wait = min(retry_delay + 2, 60)  # не ждём больше минуты
                elif "503" in exc_str or "UNAVAILABLE" in exc_str or "high demand" in exc_str:
                    wait = 15
                else:
                    wait = 2 ** attempt
                logger.warning(
                    "[%s] Attempt %d: API error. Retry in %ds. Error: %.80s",
                    self.provider_name, attempt + 1, wait, exc_str,
                )
                last_exc = exc
                await asyncio.sleep(wait)

            except APIStatusError as exc:
                # json_object не поддерживается этой моделью → отключаем
                if exc.status_code in (400, 422) and self.use_json_mode:
                    logger.warning(
                        "[%s] JSON mode rejected (HTTP %d) — switching to prompt-only.",
                        self.provider_name, exc.status_code,
                    )
                    self.use_json_mode = False
                    continue
                raise

        raise RuntimeError(
            f"[{self.provider_name}] No valid response after {max_attempts} attempts: {last_exc}"
        ) from last_exc

    async def _call(self, system: str, user: str):
        # Температура для качества:
        # - 0.4-0.6: максимальная точность JSON, меньше галлюцинаций
        # - выше → более креативный текст, но риск невалидного JSON
        if self.is_local:
            temperature = 0.5   # локальные модели нестабильны при высокой t
        elif self.is_gemini:
            temperature = 0.7   # Gemini хорошо работает при 0.7
        else:
            temperature = 0.75  # OpenAI / Groq / Kimi

        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 4096,
        }

        if self.use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        return await self.client.chat.completions.create(**kwargs)


def _parse_retry_delay(error_text: str) -> int | None:
    """Извлекает рекомендованную задержку из ответа API (retryDelay: '33s')."""
    import re
    match = re.search(r"retryDelay['\"]:\s*['\"](\d+)s", error_text)
    if match:
        return int(match.group(1))
    match = re.search(r"retry in (\d+)\.?\d*s", error_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_json(text: str) -> str:
    """Извлекает JSON из ответа LLM — убирает markdown, текст до/после."""
    text = text.strip()

    # Убираем ```json ... ``` обёртки
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # убираем ```json
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Если уже начинается с { — возвращаем как есть
    if text.startswith("{"):
        return text

    # Ищем первый { и последний соответствующий }
    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    end = -1
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    return text[start:end] if end != -1 else text[start:]
