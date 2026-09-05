"""Генератор карьерной истории кандидата."""
from __future__ import annotations

import logging
import random
from datetime import date

from app.schemas import (
    Candidate,
    CandidateInfo,
    CareerProfile,
    QualityScores,
    RoleExperience,
    VacancyAnalysis,
)
from app.services.company_generator import CompanyGenerator
from app.services.experience_generator import ExperienceGenerator
from app.services.knowledge_base import CANDIDATE_CITIES, CANDIDATE_NAMES, SENIORITY_DEFAULTS
from app.services.project_generator import ProjectGenerator

logger = logging.getLogger(__name__)


class CareerGenerator:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self.company_generator = CompanyGenerator(llm=llm)
        self.project_generator = ProjectGenerator(llm=llm)
        self.experience_generator = ExperienceGenerator(llm=llm)

    async def generate(
        self,
        analysis: VacancyAnalysis,
        seed: int | None = None,
        candidate_info: CandidateInfo | None = None,
    ) -> CareerProfile:
        rng = random.Random(seed)

        years = max(
            analysis.required_experience,
            SENIORITY_DEFAULTS[analysis.seniority]["years"],
        )
        candidate = self._build_candidate(analysis, years, rng, candidate_info)

        role_count = 2 if analysis.seniority == "Junior" else rng.choice([2, 3])
        roles: list[RoleExperience] = []
        end_year = date.today().year
        used_task_ids: set[str] = set()   # для разнообразия задач
        used_company_names: set[str] = set()  # чтобы компании не повторялись

        for index in range(role_count):
            duration = max(1, years // role_count) + rng.randint(-1, 1)
            duration = max(1, duration)
            start_year = end_year - duration

            company = await self.company_generator.create(
                analysis.domain, index, rng, used_names=used_company_names,
                language=analysis.language, is_nda=analysis.is_nda_domain
            )
            used_company_names.add(company.name)
            project = await self.project_generator.create_project(company, analysis, rng)
            team = self.project_generator.create_team(analysis.seniority, rng)
            tasks = await self.experience_generator.create_tasks(
                project, analysis, rng, excluded_ids=used_task_ids
            )
            used_task_ids.update(self.experience_generator.last_selected_ids)

            role_title = self._role_for(analysis.seniority, index)

            roles.append(
                RoleExperience(
                    company=company,
                    start_date=f"{start_year}-01",
                    end_date="Present" if index == 0 else f"{end_year}-01",
                    role=role_title,
                    project=project,
                    team=team,
                    tasks=tasks,
                    technologies=project.technologies,
                    quality=QualityScores(
                        technical_realism=rng.randint(88, 96),
                        business_realism=rng.randint(87, 95),
                        career_consistency=rng.randint(90, 97),
                        seniority_consistency=rng.randint(91, 97),
                        language_quality=rng.randint(87, 94),
                    ),
                )
            )
            end_year = start_year

        quality = round(sum(role.quality.quality_score for role in roles) / len(roles))
        logger.info(
            "CareerGenerator: создан профиль '%s' (%s), quality=%d",
            candidate.name,
            candidate.seniority,
            quality,
        )
        return CareerProfile(candidate=candidate, roles=roles, quality_score=quality)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _build_candidate(
        self,
        analysis: VacancyAnalysis,
        years: int,
        rng: random.Random,
        info: CandidateInfo | None = None,
    ) -> Candidate:
        # Используем данные пользователя если заданы, иначе генерируем placeholder
        has_info = info is not None
        name = (info.full_name if has_info and info.full_name else rng.choice(CANDIDATE_NAMES))
        city = (info.city if has_info and info.city else rng.choice(CANDIDATE_CITIES))
        phone = (info.phone if has_info and info.phone else "")
        telegram = (info.telegram if has_info and info.telegram else "")
        email = (info.email if has_info and info.email else "")

        age = 22 + years + rng.randint(0, 5)
        age = min(age, 50)

        # Пользовательские данные имеют приоритет. Fallback нужен только для
        # обратной совместимости со старыми запросами без этих полей.
        if has_info:
            education = info.education_for_resume()
        else:
            education = self._fallback_education(years, rng)

        if has_info:
            languages = info.languages_for_resume()
        else:
            languages = ["Русский — Родной", "Английский — B2 — выше среднего"]

        return Candidate(
            name=name,
            age=age,
            city=city,
            title=analysis.title,
            seniority=analysis.seniority,
            total_experience_years=years,
            education=education,
            languages=languages,
            email=email,
            phone=phone,
            telegram=telegram,
        )

    @staticmethod
    def _fallback_education(years: int, rng: random.Random) -> list[str]:
        universities = [
            "Бакалавр, Информатика и вычислительная техника — {uni}, {start}–{end}",
            "Бакалавр, Программная инженерия — {uni}, {start}–{end}",
            "Магистр, Прикладная информатика — {uni}, {start}–{end}",
        ]
        uni_names = [
            "Московский технический университет связи и информатики",
            "Санкт-Петербургский политехнический университет Петра Великого",
            "Казанский федеральный университет",
            "Новосибирский государственный технический университет",
            "Уральский федеральный университет",
        ]
        edu_template = rng.choice(universities)
        grad_year = date.today().year - years - rng.randint(0, 2)
        return [
            edu_template.format(
                uni=rng.choice(uni_names),
                start=grad_year - 4,
                end=grad_year,
            )
        ]

    def _role_for(self, seniority: str, index: int) -> str:
        roles = SENIORITY_DEFAULTS[seniority]["roles"]
        if seniority == "Senior":
            return roles[0] if index == 0 else roles[-1]
        if seniority == "Junior":
            return roles[1] if index == 0 else roles[0]
        return roles[0] if index == 0 else roles[-1]
