"""PDF валидатор — проверяет качество сгенерированного PDF."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Минимальный размер PDF (Playwright-рендер обычно > 50KB)
_MIN_SIZE_PLAYWRIGHT = 10_000
_MIN_SIZE_REPORTLAB = 1_000

# Служебные метки, которых не должно быть в документе
_FORBIDDEN_LABELS = [
    "AI Generated", "Synthetic", "Generated Resume", "Fictional",
    "Sample Resume", "Example Resume", "Demo Resume", "Test Resume",
    "DRAFT", "WATERMARK",
    "Сгенерировано ИИ", "Синтетическое резюме", "Черновик",
]

# Обязательные секции в тексте PDF
_REQUIRED_SECTIONS = ["Опыт работы", "Ключевые навыки", "Образование"]


class PdfValidator:
    def validate(self, pdf_path: Path) -> list[str]:
        issues: list[str] = []

        # ── Файл существует ───────────────────────────────────────────────────
        if not pdf_path.exists():
            return ["PDF-файл не существует."]

        size = pdf_path.stat().st_size
        if size < _MIN_SIZE_REPORTLAB:
            issues.append(f"PDF-файл слишком мал: {size} байт (минимум {_MIN_SIZE_REPORTLAB}).")
            return issues  # бессмысленно продолжать

        # Предупреждение если ReportLab fallback (маленький размер)
        if size < _MIN_SIZE_PLAYWRIGHT:
            logger.warning(
                "PDF size %d bytes — возможно использован ReportLab fallback (не Playwright).",
                size,
            )

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))

            # ── Страницы ──────────────────────────────────────────────────────
            page_count = len(reader.pages)
            if page_count == 0:
                issues.append("В PDF нет страниц.")
                return issues

            if page_count > 4:
                issues.append(f"В PDF слишком много страниц: {page_count} (ожидается 1–4).")

            # ── Текст ─────────────────────────────────────────────────────────
            full_text = ""
            blank_pages = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if len(page_text.strip()) < 50:
                    blank_pages += 1
                full_text += page_text + "\n"

            if blank_pages > 0:
                issues.append(f"В PDF обнаружено пустых страниц: {blank_pages}.")

            if len(full_text.strip()) < 100:
                issues.append("В PDF недостаточно извлекаемого текста.")

            # ── Запрещённые метки ─────────────────────────────────────────────
            full_text_lower = full_text.lower()
            for label in _FORBIDDEN_LABELS:
                if label.lower() in full_text_lower:
                    issues.append(f"В PDF обнаружена запрещённая метка: «{label}».")

            # ── Обязательные секции ───────────────────────────────────────────
            missing_sections = [
                s for s in _REQUIRED_SECTIONS if s.lower() not in full_text_lower
            ]
            if missing_sections:
                logger.warning("PDF missing sections: %s", missing_sections)
                # Не добавляем в issues — ReportLab fallback может менять форматирование

            logger.info(
                "PDF validation: %d pages, %d chars, %d issues",
                page_count,
                len(full_text),
                len(issues),
            )

        except Exception as exc:
            issues.append(f"Не удалось открыть или прочитать PDF: {exc}")

        return issues
