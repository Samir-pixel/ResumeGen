"""Генератор проектов и команд."""
from __future__ import annotations

import logging
import random
from pathlib import Path

from app.schemas import Company, Project, Team, VacancyAnalysis
from app.services.knowledge_base import DEFAULT_DOMAIN, DOMAIN_PATTERNS
from app.services.knowledge_base_ru import ru_domain_data

logger = logging.getLogger(__name__)

_PROJ_PROMPT = Path("prompts/project_generator/system.md")


class ProjectGenerator:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None

    async def create_project(
        self, company: Company, analysis: VacancyAnalysis, rng: random.Random
    ) -> Project:
        if self.llm:
            return await self._create_with_llm(company, analysis)
        return self._create_heuristic(company, analysis, rng)

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _create_with_llm(self, company: Company, analysis: VacancyAnalysis) -> Project:
        system = self._load_prompt()
        context = (
            f"Компания: {company.name}\n"
            f"Отрасль: {company.industry}\n"
            f"Описание бизнеса: {company.business_description}\n"
            f"Обязательные технологии: {', '.join(analysis.required_skills)}\n"
            f"Уровень кандидата: {analysis.seniority}\n"
            "Создай реалистичный проект этой компании. Вся человеческая проза "
            "в результате должна быть на русском языке."
        )
        logger.info("ProjectGenerator: LLM call (%s)", company.name)
        return await self.llm.generate(system, context, Project)

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _PROJ_PROMPT.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = (
                    "Создавай реалистичные описания проектов для резюме. "
                    "Вся человеческая проза должна быть на русском языке. "
                    "Сохраняй официальные названия технологий."
                )
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _create_heuristic(
        self, company: Company, analysis: VacancyAnalysis, rng: random.Random
    ) -> Project:
        domain_data = DOMAIN_PATTERNS.get(company.industry, DOMAIN_PATTERNS[DEFAULT_DOMAIN])
        integrations = rng.sample(
            domain_data["integrations"],
            k=min(2, len(domain_data["integrations"])),
        )
        technologies = self._technology_stack(analysis.required_skills, company.industry)
        russian = analysis.language == "ru"

        if russian:
            ru_data = ru_domain_data(company.industry)
            product = rng.choice(ru_data["products"])
            users = ru_data["users"]
            integrations = list(dict.fromkeys(integrations + ["сервис уведомлений"]))
            name = product[0].upper() + product[1:]
            description = (
                f"{name}: обработка обращений, отслеживание изменений статусов "
                f"и хранение истории операций. Пользователи — {users}."
            )
            business_purpose = (
                f"Сократить ручную работу в процессах сферы «{company.sector}» "
                "и сделать операции прозрачными."
            )
            scale_options = [
                f"{rng.randint(5, 50)} тыс. записей в месяц",
                f"{rng.randint(200, 1000)} активных пользователей в день",
                "мультитенантная B2B-инсталляция",
                f"{rng.randint(1, 10)} млн событий в сутки",
            ]
            modules = [
                "API-сервис", "движок бизнес-процессов", "административная панель",
                "модуль отчётности", "интеграционный слой",
            ]
            architecture = rng.choice([
                "Модульный монолит с изолированными доменными модулями и асинхронной обработкой задач.",
                "Сервисная архитектура с общими PostgreSQL и Redis.",
                "Слоистое Django-приложение с Celery-воркерами и REST API.",
            ])
        else:
            product = rng.choice(domain_data["products"])
            users = _users_for(company.industry)
            integrations = list(dict.fromkeys(integrations + ["notification service"]))
            name = product.title()
            description = (
                f"A {product} used by {users} to manage requests, "
                "track status changes, and maintain a reliable audit trail."
            )
            business_purpose = (
                f"Reduce manual effort in {company.sector.lower()} workflows "
                "and improve operational visibility."
            )
            scale_options = [
                f"{rng.randint(5, 50)}k monthly records",
                f"{rng.randint(200, 1000)} daily active internal users",
                "multi-tenant B2B deployment",
                f"{rng.randint(1, 10)} million events per day",
            ]
            modules = [
                "API service", "workflow engine", "admin panel",
                "reporting module", "integration layer",
            ]
            architecture = rng.choice([
                "Modular monolith with isolated domain modules and async task processing.",
                "Service-oriented architecture with shared PostgreSQL and Redis.",
                "Layered Django application with Celery workers and a REST API.",
            ])

        return Project(
            name=name,
            description=description,
            business_purpose=business_purpose,
            target_users=users,
            scale=rng.choice(scale_options),
            modules=modules,
            architecture=architecture,
            integrations=integrations,
            databases=["PostgreSQL"] + (["Redis"] if "Redis" in technologies else []),
            infrastructure=["Docker"] + (
                ["Kubernetes"] if analysis.seniority == "Senior" else []
            ),
            technologies=technologies,
        )

    def create_team(self, seniority: str, rng: random.Random) -> Team:
        structures = {
            "Junior": {
                "structures": [
                    "Небольшая продуктовая команда",
                    "Команда backend-разработки",
                    "Кросс-функциональная продуктовая команда",
                ],
                "role_options": [
                    ["Tech Lead", "2 backend-разработчика", "Frontend-разработчик", "QA-инженер"],
                    ["Старший backend-разработчик", "Backend-разработчик", "QA-инженер"],
                    ["Tech Lead", "3 backend-разработчика", "QA-инженер"],
                ],
                "candidate_role": (
                    "Выполнял поставленные backend-задачи под code review, "
                    "исправлял ошибки и писал модульные тесты."
                ),
            },
            "Middle": {
                "structures": [
                    "Продуктовая команда",
                    "Кросс-функциональная команда",
                    "Команда backend-разработки",
                ],
                "role_options": [
                    ["Tech Lead", "3 backend-разработчика", "2 frontend-разработчика", "QA-инженер"],
                    [
                        "Старший backend-разработчик",
                        "2 backend-разработчика",
                        "Frontend-разработчик",
                        "QA-инженер",
                    ],
                    ["Tech Lead", "2 backend-разработчика", "QA-инженер", "DevOps-инженер"],
                ],
                "candidate_role": (
                    "Разрабатывал backend-функциональность и интеграции сервисов, "
                    "участвовал в проектировании и code review."
                ),
            },
            "Senior": {
                "structures": [
                    "Платформенная команда",
                    "Команда backend-разработки",
                    "Продуктовая инженерная команда",
                ],
                "role_options": [
                    [
                        "Tech Lead",
                        "4 backend-разработчика",
                        "2 frontend-разработчика",
                        "QA-инженер",
                        "DevOps-инженер",
                    ],
                    [
                        "Старший backend-разработчик",
                        "3 backend-разработчика",
                        "QA-инженер",
                        "DevOps-инженер",
                    ],
                    [
                        "Tech Lead",
                        "3 backend-разработчика",
                        "2 frontend-разработчика",
                        "QA Lead",
                    ],
                ],
                "candidate_role": (
                    "Отвечал за техническое проектирование ключевых backend-подсистем, "
                    "проводил code review и помогал разработчикам уровня Middle."
                ),
            },
        }
        cfg = structures[seniority]
        roles = rng.choice(cfg["role_options"])
        structure = rng.choice(cfg["structures"])

        return Team(
            size=rng.randint(5, 12),
            roles=roles,
            structure=structure,
            candidate_role=cfg["candidate_role"],
            collaboration=(
                "Работал с продуктовой командой, QA и frontend-разработчиками: "
                "участвовал в планировании, реализации, code review и выпуске релизов."
            ),
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _technology_stack(self, required_skills: list[str], domain: str) -> list[str]:
        # Базовый стек на основе фреймворка
        if "Django" in required_skills or "DRF" in required_skills:
            base = ["Python", "Django", "DRF", "PostgreSQL", "Celery", "Redis", "Docker", "Pytest"]
        else:
            base = ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Alembic", "Redis", "Docker", "Pytest"]

        # Добавляем из required_skills
        for skill in required_skills:
            if skill not in base:
                base.append(skill)

        # Добавляем Kafka для streaming-доменов
        if domain in ("FinTech", "Telecom", "iGaming") and "Kafka" not in base:
            base.insert(-1, "Kafka")

        return base[:12]


def _users_for(domain: str) -> str:
    mapping = {
        "FinTech": "operations analysts, loan officers, and compliance teams",
        "E-commerce": "marketplace sellers, catalog managers, and fulfillment teams",
        "SaaS": "business users, support agents, and account managers",
        "Logistics": "dispatch managers, warehouse operators, and drivers",
        "Healthcare": "medical staff, patients, and clinic administrators",
        "ERP": "procurement specialists, accountants, and operations managers",
        "EdTech": "learners, course instructors, and training managers",
        "iGaming": "players, casino operators, and fraud analysts",
        "Telecom": "mobile subscribers, customer service agents, and network engineers",
    }
    return mapping.get(domain, "internal users and operations teams")
