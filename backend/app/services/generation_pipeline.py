"""Основной пайплайн генерации резюме."""
from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from app.core.config import Settings
from app.repositories.file_repository import FileGenerationRepository
from app.schemas import CandidateInfo, GenerationRun, GenerationStatus
from app.services.career_generator import CareerGenerator
from app.services.consistency_validator import ConsistencyValidator
from app.services.html_renderer import HtmlRenderer
from app.services.llm.base import LLMProvider, create_provider
from app.services.pdf_renderer import PdfRenderer
from app.services.pdf_validator import PdfValidator
from app.services.realism_validator import RealismValidator
from app.services.quality_scorer import PASS_THRESHOLD, ResumeQualityScorer
from app.services.resume_critic import ResumeCritic
from app.services.resume_writer import ResumeWriter
from app.services.vacancy_analyzer import VacancyAnalyzer

logger = logging.getLogger(__name__)


class GenerationPipeline:
    def __init__(self, settings: Settings, repository: FileGenerationRepository) -> None:
        self.settings = settings
        self.repository = repository

        # Создаём LLM провайдер (None если LLM_PROVIDER=heuristic)
        llm: LLMProvider | None = create_provider(settings)

        self.vacancy_analyzer = VacancyAnalyzer(llm=llm)
        self.career_generator = CareerGenerator(llm=llm)
        self.consistency_validator = ConsistencyValidator()
        self.realism_validator = RealismValidator()
        self.resume_writer = ResumeWriter(llm=llm)
        self.resume_critic = ResumeCritic(llm=llm)
        self.html_renderer = HtmlRenderer(settings.templates_dir)
        self.pdf_renderer = PdfRenderer()
        self.pdf_validator = PdfValidator()

        # Имя модели для логирования
        self.model_name = (
            f"{settings.llm_provider}:{getattr(llm, 'model', settings.llm_model)}"
            if llm
            else "heuristic"
        )

    async def run(
        self,
        generation_id: str,
        vacancy: str,
        candidate_info: CandidateInfo | None = None,
    ) -> GenerationRun:
        """Запускает полный пайплайн генерации."""
        run = self.repository.get(generation_id)
        if run is None:
            from app.schemas import GenerationRun as GR
            run = GR(generation_id=generation_id, vacancy=vacancy)

        # Подставляем личные данные из run если не переданы явно
        if candidate_info is None and run.candidate_info:
            candidate_info = run.candidate_info

        run.model = self.model_name
        run.prompt_version = self.settings.prompt_version
        run.status = GenerationStatus.analyzing_vacancy
        self.repository.save(run)

        try:
            # ── 1. Анализ вакансии ────────────────────────────────────────────
            analysis = await self._stage(
                run,
                "Анализ вакансии",
                GenerationStatus.analyzing_vacancy,
                lambda: self.vacancy_analyzer.analyze(vacancy),
            )
            run.vacancy_analysis = analysis

            # ── 2. Генерация кандидата и карьеры ─────────────────────────────
            run.status = GenerationStatus.generating_candidate
            self.repository.save(run)
            profile = await self._stage(
                run,
                "Формирование карьерного профиля",
                GenerationStatus.generating_companies,
                lambda: self.career_generator.generate(analysis, candidate_info=candidate_info),
            )

            # ── 3. Валидация консистентности (с регенерацией) ─────────────────
            for attempt in range(self.settings.max_consistency_retries + 1):
                issues = await self._stage(
                    run,
                    "Проверка связности данных",
                    GenerationStatus.validating,
                    lambda current_profile=profile: self.consistency_validator.validate(
                        current_profile
                    ),
                )
                profile.issues = issues

                if not issues:
                    break

                if attempt < self.settings.max_consistency_retries:
                    logger.warning(
                        "Consistency issues (attempt %d): %s — regenerating career",
                        attempt + 1,
                        "; ".join(issues),
                    )
                    profile = await self._stage(
                        run,
                        f"Повторное формирование карьеры (попытка {attempt + 2})",
                        GenerationStatus.generating_companies,
                        lambda: self.career_generator.generate(
                            analysis,
                            candidate_info=candidate_info,
                        ),
                    )
                else:
                    # Последняя попытка — продолжаем с issues
                    logger.error("Consistency not resolved after retries: %s", "; ".join(issues))

            run.career_profile = profile

            # ── 4. Проверка реализма (RealismValidator §46) ───────────────────
            realism = await self._stage(
                run,
                "Проверка реалистичности",
                GenerationStatus.validating,
                lambda: self.realism_validator.validate(profile),
            )
            if realism.score < 70:
                logger.warning(
                    "Realism score low: %d (issues: %s)",
                    realism.score,
                    "; ".join(realism.issues[:3]),
                )
            else:
                logger.info("Realism score: %d", realism.score)

            # ── 5. Написание резюме ───────────────────────────────────────────
            resume = await self._stage(
                run,
                "Подготовка текста резюме",
                GenerationStatus.writing_resume,
                lambda: self.resume_writer.write(analysis, profile, candidate_info=candidate_info),
            )
            run.resume = resume

            # Language realism check on written resume
            lang_realism = await self._stage(
                run,
                "Проверка качества русского текста",
                GenerationStatus.criticizing,
                lambda: self.realism_validator.validate(profile, resume),
            )
            logger.info("Language realism score: %d", lang_realism.language_realism)

            # ── 6. Оценка по рубрике + доработка до порога ───────────────────
            threshold = min(self.settings.critic_threshold, PASS_THRESHOLD)
            scorer = ResumeQualityScorer()
            for iteration in range(self.settings.max_critic_iterations):
                critic = await self._stage(
                    run,
                    f"Редакторская проверка (попытка {iteration + 1})",
                    GenerationStatus.criticizing,
                    lambda current_resume=resume: self.resume_critic.review(
                        analysis,
                        profile,
                        current_resume,
                    ),
                )
                run.critic = critic

                if critic.overall_score >= threshold:
                    logger.info(
                        "Quality score %d >= threshold %d — OK",
                        critic.overall_score,
                        threshold,
                    )
                    break

                if iteration >= self.settings.max_critic_iterations - 1:
                    logger.warning(
                        "Финальный quality score: %d (порог %d). Замечания: %s",
                        critic.overall_score,
                        threshold,
                        "; ".join(critic.issues[:5]),
                    )
                    break

                remarks = list(critic.issues)
                logger.warning(
                    "Quality score %d < %d — доработка %d. Замечания: %s",
                    critic.overall_score,
                    threshold,
                    iteration + 2,
                    "; ".join(remarks[:5]),
                )
                if scorer.should_regenerate_career(critic):
                    profile = await self._stage(
                        run,
                        f"Пересборка карьеры по замечаниям (попытка {iteration + 2})",
                        GenerationStatus.generating_companies,
                        lambda: self.career_generator.generate(
                            analysis,
                            candidate_info=candidate_info,
                        ),
                    )
                    run.career_profile = profile

                resume = await self._stage(
                    run,
                    f"Доработка резюме (попытка {iteration + 2})",
                    GenerationStatus.writing_resume,
                    lambda current_profile=profile, current_remarks=remarks: (
                        self.resume_writer.write(
                            analysis,
                            current_profile,
                            candidate_info=candidate_info,
                            feedback=current_remarks,
                        )
                    ),
                )
                run.resume = resume

            # ── 7. HTML рендеринг ─────────────────────────────────────────────
            html_path = self.settings.generated_storage_dir / f"{run.generation_id}.html"
            tmpl = run.template or "modern"
            html = await self._stage(
                run,
                "Создание предпросмотра",
                GenerationStatus.rendering_pdf,
                lambda: self.html_renderer.render(run.resume, html_path, tmpl),
            )
            run.html_path = html_path

            # ── 7. PDF рендеринг ──────────────────────────────────────────────
            pdf_filename = self._pdf_filename(
                run.resume.header["name"],
                analysis.title,
                run.generation_id,
            )
            pdf_path = self.settings.pdf_storage_dir / pdf_filename

            run.status = GenerationStatus.rendering_pdf
            self.repository.save(run)
            logger.info("PDF rendering: %s", pdf_path)
            run.pdf_path = await self.pdf_renderer.render(html, run.resume, pdf_path)
            self._add_stage(run, "Создание PDF", "completed")
            self.repository.save(run)

            # ── 8. Валидация PDF ──────────────────────────────────────────────
            pdf_issues = await self._stage(
                run,
                "Проверка PDF",
                GenerationStatus.validating_pdf,
                lambda: self.pdf_validator.validate(run.pdf_path),
            )
            if pdf_issues:
                # Некритичные проблемы — логируем, но не останавливаем
                logger.warning("PDF validation warnings: %s", "; ".join(pdf_issues))

            # ── Завершение ────────────────────────────────────────────────────
            run.status = GenerationStatus.completed
            run.quality_score = run.critic.overall_score if run.critic else run.career_profile.quality_score
            run.resume_id = run.generation_id
            run.pdf_url = f"/api/v1/resumes/{run.generation_id}/pdf"
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)
            self.repository.save(run)
            logger.info(
                "Generation %s completed. Quality: %d",
                run.generation_id,
                run.quality_score,
            )
            return run

        except Exception as exc:
            logger.exception("Generation %s failed: %s", run.generation_id, exc)
            return self.repository.mark_failed(run, str(exc))

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _stage(self, run: GenerationRun, name: str, status: GenerationStatus, action):
        """Выполняет один этап пайплайна: обновляет статус, запускает action, сохраняет."""
        run.status = status
        started_at = datetime.now(UTC).replace(tzinfo=None)
        self.repository.save(run)
        logger.info("Stage started: %s", name)

        # Поддержка как async, так и sync actions (включая lambdas, возвращающие корутины)
        import inspect
        result_or_coro = action()
        if inspect.isawaitable(result_or_coro):
            result = await result_or_coro
        else:
            result = result_or_coro

        self._add_stage(run, name, "completed", started_at)
        self.repository.save(run)
        logger.info("Stage done: %s", name)
        return result

    def _add_stage(
        self,
        run: GenerationRun,
        name: str,
        status: str,
        started_at: datetime | None = None,
    ) -> None:
        entry: dict[str, str] = {
            "stage": name,
            "status": status,
            "completed_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        }
        if started_at:
            entry["started_at"] = started_at.isoformat()
        run.stages.append(entry)

    def _pdf_filename(self, name: str, title: str, generation_id: str) -> str:
        raw = f"{name}_{title}_{generation_id[:5]}"
        slug = re.sub(r"[^A-Za-zА-Яа-яёЁ0-9]+", "_", raw).strip("_")
        # Транслитерация кириллицы
        slug = _transliterate(slug)
        return f"{slug}.pdf"


def _transliterate(text: str) -> str:
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    result = []
    for ch in text:
        lower = ch.lower()
        if lower in mapping:
            replacement = mapping[lower]
            result.append(replacement.upper() if ch.isupper() else replacement)
        else:
            result.append(ch)
    return ''.join(result)
