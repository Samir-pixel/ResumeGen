"""Сервис написания резюме — превращает структурированный профиль в профессиональный текст."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from pydantic import BaseModel

from app.schemas import (
    CandidateInfo,
    CareerProfile,
    ExperienceTask,
    ResumeDocument,
    ResumeExperience,
    RoleExperience,
    VacancyAnalysis,
)

logger = logging.getLogger(__name__)

_WRITER_PROMPT = Path("prompts/resume_writer/system.md")

_RUSSIAN_LOCALIZATION_PROMPT = """Ты — технический редактор и переводчик.
Получишь ResumeDocument в JSON. Верни ResumeDocument с той же структурой и теми же фактами.

Переведи на естественный профессиональный русский язык только человеческую прозу:
target_position, summary, названия групп skills, role, sector, location,
company_description, project_description, team и bullets.

Не переводи и не изменяй: JSON keys, имена людей, названия компаний и продуктов,
email, Telegram, числа, даты, метрики, названия технологий и аббревиатуры
(Python, FastAPI, PostgreSQL, REST API, CI/CD, SLA, B2B и подобные).
Не добавляй и не удаляй роли, bullets, навыки или факты.
education и languages копируй дословно.
В обычной прозе не должно остаться английских предложений.
Верни только валидный JSON без Markdown и пояснений."""


class _ResumeWriterInput(BaseModel):
    """Передаётся LLM для написания резюме."""
    vacancy_title: str
    vacancy_domain: str
    required_skills: list[str]
    candidate_name: str
    candidate_city: str
    candidate_email: str
    candidate_phone: str
    candidate_seniority: str
    candidate_experience_years: int
    roles_summary: list[dict]  # компактное представление ролей
    education: list[str]
    languages: list[str]


class _BulletSet(BaseModel):
    """LLM генерирует bullets для одной роли."""
    summary: str
    bullets: list[str]


class ResumeWriter:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None

    async def write(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        candidate_info: CandidateInfo | None = None,
    ) -> ResumeDocument:
        if self.llm:
            return await self._write_with_llm(analysis, profile, candidate_info)
        return self._write_heuristic(analysis, profile, candidate_info)

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _write_with_llm(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        candidate_info: CandidateInfo | None = None,
    ) -> ResumeDocument:
        system = self._load_prompt()
        candidate = profile.candidate

        # Формируем компактные данные для промпта
        roles_summary = []
        for role in profile.roles:
            roles_summary.append({
                "company": role.company.name,
                "company_industry": role.company.industry,
                "company_desc": role.company.business_description,
                "role": role.role,
                "dates": f"{role.start_date} — {role.end_date}",
                "sector": role.company.sector,
                "location": role.company.location,
                "project": role.project.name,
                "project_desc": role.project.description,
                "team": f"{role.team.structure}: {', '.join(role.team.roles)}",
                "candidate_role_desc": role.team.candidate_role,
                "technologies": role.technologies,
                "tasks": [
                    {
                        "problem": t.problem,
                        "task": t.task,
                        "actions": t.actions,
                        "technologies": t.technologies,
                        "reason": t.reason,
                        "result": t.result,
                        "business_impact": t.business_impact,
                    }
                    for t in role.tasks
                ],
            })

        context = (
            f"Целевая должность: {analysis.title}\n"
            f"Домен: {analysis.domain}\n"
            f"Обязательные навыки: {', '.join(analysis.required_skills)}\n"
            f"Приоритетные требования: {', '.join(analysis.priority_requirements)}\n\n"
            f"Кандидат: {candidate.name}, {candidate.city}, {candidate.email}, {candidate.phone}\n"
            f"Уровень: {candidate.seniority}, опыт: {candidate.total_experience_years} лет\n"
            f"Образование (копировать дословно): {'; '.join(candidate.education)}\n"
            f"Языки (копировать дословно): {', '.join(candidate.languages)}\n\n"
            f"Карьерный профиль:\n{_format_roles_for_prompt(roles_summary)}"
        )

        logger.info("ResumeWriter: LLM call")
        resume = await self.llm.generate(system, context, ResumeDocument)
        expected_experience_count = len(resume.experience)

        # Some smaller models copy English intermediate descriptions despite a
        # Russian system prompt. A focused localization pass is more reliable
        # than accepting a mixed-language final document.
        for attempt in range(2):
            ratio = _russian_prose_ratio(resume)
            if ratio >= 0.62:
                break
            logger.warning(
                "Resume contains too much non-Russian prose (ratio=%.2f); "
                "running localization pass %d",
                ratio,
                attempt + 1,
            )
            localized = await self.llm.generate(
                _RUSSIAN_LOCALIZATION_PROMPT,
                json.dumps(resume.model_dump(mode="json"), ensure_ascii=False),
                ResumeDocument,
            )
            if len(localized.experience) != expected_experience_count:
                logger.warning(
                    "Localization changed experience count; keeping previous document"
                )
                break
            resume = localized
        if _russian_prose_ratio(resume) < 0.62:
            logger.error(
                "LLM localization did not produce Russian prose; using deterministic "
                "Russian writer fallback"
            )
            return self._write_heuristic(analysis, profile, candidate_info)

        # LLMs occasionally omit contact fields from the free-form header dict.
        # Keep personal data deterministic and independent from model output.
        info = candidate_info or CandidateInfo()
        resume.header = {
            **resume.header,
            "name": info.full_name or candidate.name,
            "city": info.city or candidate.city,
            "phone": info.phone or candidate.phone,
            "email": info.email or candidate.email,
        }
        telegram = info.telegram or candidate.telegram
        if telegram:
            resume.header["telegram"] = telegram
        # Structured personal facts are immutable: the language model writes
        # prose but must never alter education or language proficiency.
        resume.education = list(candidate.education)
        resume.languages = list(candidate.languages)
        resume.target_position = analysis.title
        for experience, role in zip(resume.experience, profile.roles, strict=False):
            experience.company = role.company.name
            experience.technologies = list(role.technologies)
            experience.dates = (
                f"{role.start_date[:4]} — "
                f"{'н. в.' if role.end_date == 'Present' else role.end_date[:4]}"
            )
            experience.role = _localize_role(role.role)
            experience.sector = _localize_sector(experience.sector)
            experience.location = _localize_location(experience.location)
            experience.dates = experience.dates.replace("Present", "н. в.")

        return resume

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _WRITER_PROMPT.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = _DEFAULT_WRITER_PROMPT
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _write_heuristic(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        candidate_info: CandidateInfo | None = None,
    ) -> ResumeDocument:
        candidate = profile.candidate
        skills = self._build_skills(analysis, profile)
        experience = [self._write_role(role, analysis) for role in profile.roles]
        summary = self._build_summary(candidate, analysis, profile)

        # Личные данные: приоритет — данные пользователя, затем — сгенерированные
        info = candidate_info or CandidateInfo()
        header: dict[str, str] = {
            "name": info.full_name or candidate.name,
            "city": info.city or candidate.city,
            "phone": info.phone or candidate.phone,
            "email": info.email or candidate.email,
        }
        if info.telegram:
            header["telegram"] = info.telegram
        elif candidate.telegram:
            header["telegram"] = candidate.telegram

        return ResumeDocument(
            header=header,
            target_position=analysis.title,
            summary=summary,
            skills=skills,
            experience=experience,
            education=candidate.education,
            languages=candidate.languages,
        )

    _SUMMARY_OPENERS = [
        "{seniority} backend-разработчик с опытом {years} лет",
        "Python backend-инженер с {years}-летним опытом коммерческой разработки",
        "Backend-разработчик уровня {seniority}, опыт — {years} лет",
        "Инженер-программист с фокусом на Python backend и опытом {years} лет",
    ]

    _SUMMARY_DOMAIN_PHRASES = {
        "FinTech": "финансовых сервисов и платёжных систем",
        "E-commerce": "электронной коммерции и маркетплейсов",
        "SaaS": "B2B SaaS-продуктов",
        "B2B SaaS": "B2B SaaS-продуктов",
        "iGaming": "высоконагруженных игровых платформ",
        "Healthcare": "цифровой медицины",
        "HealthTech": "цифровой медицины",
        "EdTech": "образовательных платформ",
        "Logistics": "логистики и автоматизации цепочек поставок",
        "ERP": "корпоративных информационных систем",
        "AdTech": "маркетинговой аналитики и рекламных платформ",
        "Telecom": "облачной телефонии и телеком-сервисов",
        "Crypto": "криптовалютных и Web3-сервисов",
    }

    _SUMMARY_CLOSERS = [
        "Уделяет внимание качеству кода, надёжности интеграций и сопровождаемости сервисов.",
        "Выбирает прагматичные технические решения и подтверждает их измеримыми результатами.",
        "Работает со всем backend-стеком: от проектирования API до оптимизации баз данных.",
        "Развивает наблюдаемость и автоматизированное тестирование с первых этапов разработки.",
    ]

    def _build_summary(
        self, candidate, analysis: VacancyAnalysis, profile: CareerProfile
    ) -> str:
        all_techs = list(dict.fromkeys(
            t for role in profile.roles for t in role.technologies
        ))
        core_stack = ", ".join(all_techs[:4])
        years = candidate.total_experience_years
        seniority = candidate.seniority
        domain_phrase = self._SUMMARY_DOMAIN_PHRASES.get(
            analysis.domain, f"цифровых продуктов в сфере {analysis.domain}"
        )

        # Детерминированный выбор на основе имени кандидата
        name_hash = sum(ord(c) for c in candidate.name)
        opener = self._SUMMARY_OPENERS[name_hash % len(self._SUMMARY_OPENERS)]
        closer = self._SUMMARY_CLOSERS[name_hash % len(self._SUMMARY_CLOSERS)]

        seniority_ru = {"Junior": "Junior", "Middle": "Middle", "Senior": "Senior"}[seniority]
        opener = opener.format(seniority=seniority_ru, years=years)

        # Собираем специфику из ролей
        has_async = any(
            t in role.technologies
            for role in profile.roles
            for t in ("Celery", "Kafka", "RabbitMQ")
        )
        has_caching = any(
            "Redis" in role.technologies
            for role in profile.roles
        )
        aspects = []
        if has_async:
            aspects.append("асинхронной обработкой задач")
        if has_caching:
            aspects.append("стратегиями кэширования")
        aspects_str = " и ".join(aspects[:2]) if aspects else "интеграциями между сервисами"

        return (
            f"{opener} в области {domain_phrase}. "
            f"Основной стек: {core_stack}. "
            f"Проектирует API, работает с {aspects_str} и оптимизацией баз данных. "
            f"{closer}"
        )

    def _build_skills(
        self, analysis: VacancyAnalysis, profile: CareerProfile
    ) -> dict[str, list[str]]:
        all_techs = list(dict.fromkeys(
            t for role in profile.roles for t in role.technologies
        ))

        backend_keys = {"Python", "FastAPI", "Django", "DRF", "Flask"}
        data_keys = {"PostgreSQL", "MySQL", "MongoDB", "SQLAlchemy", "Alembic", "Elasticsearch"}
        queue_keys = {"Redis", "Celery", "Kafka", "RabbitMQ"}
        infra_keys = {"Docker", "Docker Compose", "Kubernetes", "AWS S3", "AWS", "GCP", "Terraform"}

        backend = [t for t in all_techs if t in backend_keys]
        data = [t for t in all_techs if t in data_keys]
        queues = [t for t in all_techs if t in queue_keys]
        infra = [t for t in all_techs if t in infra_keys]

        # Добавляем из требований вакансии если нет
        for skill in analysis.required_skills[:5]:
            if skill in backend_keys and skill not in backend:
                backend.append(skill)
            elif skill in data_keys and skill not in data:
                data.append(skill)

        result = {}
        if backend:
            result["Backend-разработка"] = backend[:6]
        if data:
            result["Данные и хранение"] = data[:5]
        if queues:
            result["Очереди и асинхронность"] = queues[:4]
        if infra:
            result["Инфраструктура"] = infra[:4]
        result["Качество и практики"] = ["Pytest", "Code review", "Проектирование REST API", "Git"]
        return result

    def _write_role(self, role: RoleExperience, analysis: VacancyAnalysis) -> ResumeExperience:
        bullets = [self._task_to_bullet(task, role) for task in role.tasks]
        role_ru = _localize_role(role.role)
        domain_phrase = self._SUMMARY_DOMAIN_PHRASES.get(
            analysis.domain,
            f"цифровых продуктов в сфере {analysis.domain}",
        )
        techs = ", ".join(role.technologies[:5])
        team_str = (
            f"Кросс-функциональная команда из {role.team.size} специалистов. "
            f"Зона ответственности: backend-разработка, оценка задач и участие в code review."
        )
        return ResumeExperience(
            company=role.company.name,
            sector=_localize_sector(role.company.sector),
            location=_localize_location(role.company.location),
            dates=(
                f"{role.start_date[:4]} — "
                f"{'н. в.' if role.end_date == 'Present' else role.end_date[:4]}"
            ),
            role=role_ru,
            company_description=role.company.business_description or (
                f"{role.company.name} — компания, развивающая продукты в области "
                f"{domain_phrase}."
            ),
            project_description=role.project.description or (
                f"Разработка и развитие проекта «{role.project.name}» для автоматизации "
                f"ключевых бизнес-процессов. Основной стек: {techs}."
            ),
            team=team_str,
            bullets=bullets,
            technologies=role.technologies,
        )

    # Глаголы для перевода imperative → past tense
    _VERB_MAP = {
        "Add": "Added", "Apply": "Applied", "Audit": "Audited",
        "Build": "Built", "Benchmark": "Benchmarked",
        "Configure": "Configured", "Consolidate": "Consolidated",
        "Create": "Created", "Coordinate": "Coordinated",
        "Decouple": "Decoupled", "Design": "Designed", "Develop": "Developed",
        "Enable": "Enabled", "Establish": "Established", "Evaluate": "Evaluated",
        "Extend": "Extended", "Extract": "Extracted",
        "Implement": "Implemented", "Improve": "Improved", "Introduce": "Introduced",
        "Integrate": "Integrated", "Identify": "Identified",
        "Map": "Mapped", "Migrate": "Migrated", "Monitor": "Monitored", "Move": "Moved",
        "Optimise": "Optimised", "Optimize": "Optimized",
        "Refactor": "Refactored", "Replace": "Replaced", "Restructure": "Restructured",
        "Set": "Set", "Schedule": "Scheduled", "Split": "Split",
        "Track": "Tracked", "Test": "Tested",
        "Update": "Updated",
        "Version": "Versioned", "Validate": "Validated",
        "Write": "Wrote", "Wrap": "Wrapped",
    }

    def _task_to_bullet(self, task: ExperienceTask, role: RoleExperience) -> str:
        """Создаёт русскоязычный bullet без переноса английских шаблонных фраз."""
        source = " ".join([task.problem, task.task, *task.actions]).lower()
        technologies = task.technologies[:2] or role.technologies[:2]
        stack = " и ".join(technologies)

        if any(word in source for word in ("redis", "cache", "кэш")):
            core = f"Спроектировал стратегию кэширования с использованием {stack}"
        elif any(word in source for word in ("postgres", "sql", "database", "query")):
            core = f"Оптимизировал слой доступа к данным на базе {stack}"
        elif any(word in source for word in ("pytest", "test", "coverage")):
            core = f"Расширил автоматизированное тестирование с помощью {stack}"
        elif any(word in source for word in ("celery", "kafka", "rabbit", "queue", "async")):
            core = f"Реализовал надёжную асинхронную обработку задач на {stack}"
        elif any(word in source for word in ("monitor", "observ", "datadog", "logging")):
            core = f"Настроил мониторинг и диагностику сервисов с помощью {stack}"
        elif any(word in source for word in ("api", "integrat", "webhook")):
            core = f"Разработал и внедрил интеграцию сервисов на базе {stack}"
        else:
            core = f"Разработал backend-компонент с использованием {stack}"

        result_text = f"{task.result} {task.business_impact}"
        metric = re.search(
            r"\d+(?:[.,]\d+)?\s*(?:%|x|ms|мс|секунд[ы]?|минут[ы]?)",
            result_text,
            flags=re.IGNORECASE,
        )
        if metric:
            return f"{core}; достигнутая метрика — {metric.group(0)}."
        return f"{core}, повысив стабильность и сопровождаемость решения."

    def _to_past(self, sentence: str) -> str:
        """Преобразует первый глагол предложения в прошедшее время."""
        words = sentence.split()
        if not words:
            return sentence
        first = words[0]
        past = self._VERB_MAP.get(first)
        if past:
            words[0] = past
        return " ".join(words)


def _russian_prose_ratio(resume: ResumeDocument) -> float:
    """Share of Cyrillic letters in fields that must contain human prose."""
    prose = [
        resume.target_position,
        resume.summary,
        *resume.skills.keys(),
    ]
    for item in resume.experience:
        prose.extend(
            [
                item.role,
                item.sector,
                item.location,
                item.company_description,
                item.project_description,
                item.team,
                *item.bullets,
            ]
        )
    text = " ".join(prose)
    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text)
    if not letters:
        return 1.0
    return len(re.findall(r"[А-Яа-яЁё]", text)) / len(letters)


def _localize_role(value: str) -> str:
    replacements = {
        "Junior Python Developer": "Младший Python-разработчик",
        "Junior Backend Developer": "Младший backend-разработчик",
        "Python Developer": "Python-разработчик",
        "Python Backend Developer": "Python backend-разработчик",
        "Middle Python Developer": "Python-разработчик",
        "Middle Backend Developer": "Backend-разработчик",
        "Senior Python Developer": "Старший Python-разработчик",
        "Senior Python Backend Developer": "Старший Python backend-разработчик",
        "Senior Backend Engineer": "Старший backend-инженер",
        "Lead Backend Developer": "Ведущий backend-разработчик",
        "Backend Developer": "Backend-разработчик",
        "Backend Engineer": "Backend-инженер",
    }
    return replacements.get(value, value)


def _localize_sector(value: str) -> str:
    replacements = {
        "IT Services & Outsourcing": "ИТ-услуги и аутсорсинг",
        "B2B Software": "B2B-продукты",
        "Productivity Tools": "Инструменты для бизнеса",
        "E-commerce": "Электронная коммерция",
        "Retail Tech": "Технологии для ритейла",
        "Marketplace": "Маркетплейсы",
        "Banking": "Банковские сервисы",
        "Digital Lending": "Цифровое кредитование",
        "Payments": "Платёжные сервисы",
        "Supply Chain": "Управление цепочками поставок",
        "Last-Mile Delivery": "Последняя миля",
        "Digital Health": "Цифровая медицина",
        "Clinical Operations": "Медицинские процессы",
        "Software as a Service": "Облачные B2B-сервисы",
        "AdTech": "AdTech",
        "Telecom": "Телеком",
    }
    return replacements.get(value, value)


def _localize_location(value: str) -> str:
    replacements = {
        "Warsaw": "Варшава",
        "Kraków": "Краков",
        "Berlin": "Берлин",
        "Prague": "Прага",
        "London": "Лондон",
        "Lisbon": "Лиссабон",
        "Tallinn": "Таллин",
        "Tbilisi": "Тбилиси",
        "Kyiv": "Киев",
        "Poland": "Польша",
        "Germany": "Германия",
        "United Kingdom": "Великобритания",
        "Portugal": "Португалия",
        "Estonia": "Эстония",
        "Georgia": "Грузия",
        "Ukraine": "Украина",
        "USA": "США",
        "Remote": "Удалённо",
    }
    localized = value
    for source, target in replacements.items():
        localized = localized.replace(source, target)
    return localized


def _format_roles_for_prompt(roles_summary: list[dict]) -> str:
    lines = []
    for i, r in enumerate(roles_summary, 1):
        lines.append(f"=== Роль {i}: {r['role']} в {r['company']} ({r['dates']}) ===")
        lines.append(f"Отрасль: {r['company_industry']}, локация: {r['location']}")
        lines.append(f"Компания: {r['company_desc']}")
        lines.append(f"Проект: {r['project']} — {r['project_desc']}")
        lines.append(f"Команда: {r['team']}")
        lines.append(f"Роль кандидата: {r['candidate_role_desc']}")
        lines.append(f"Технологии: {', '.join(r['technologies'])}")
        lines.append("Задачи:")
        for j, t in enumerate(r['tasks'], 1):
            lines.append(f"  {j}. Проблема: {t['problem'][:100]}")
            lines.append(f"     Задача: {t['task'][:100]}")
            lines.append(f"     Действия: {' | '.join(a[:60] for a in t['actions'][:3])}")
            lines.append(f"     Технологии: {', '.join(t['technologies'])}")
            lines.append(f"     Причина выбора: {t['reason'][:80]}")
            lines.append(f"     Результат: {t['result'][:120]}")
        lines.append("")
    return "\n".join(lines)


_DEFAULT_WRITER_PROMPT = """Ты профессиональный автор резюме для технических специалистов.

Преобразуй структурированный карьерный профиль в профессиональное резюме на русском языке.

ПРАВИЛА:
1. Вся человеческая проза — только на русском. Не переводи компании, технологии и аббревиатуры.
2. Каждый bullet описывает действие, способ реализации и измеримый результат.
3. Summary — 3–4 конкретных предложения без саморекламы и клише.
4. Не выдумывай факты. Образование и языки копируй дословно.
5. Верни только полный ResumeDocument JSON, соответствующий схеме.
"""
