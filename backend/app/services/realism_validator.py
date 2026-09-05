"""RealismValidator — оценивает общую реалистичность сгенерированного профиля.

Отдельный слой поверх ConsistencyValidator (§46).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.schemas import CareerProfile, ResumeDocument

logger = logging.getLogger(__name__)

# Слова-маркеры нереалистичного преувеличения в тексте
_HYPE_MARKERS = [
    "revolutionary", "world-class", "cutting-edge", "state-of-the-art",
    "next-generation", "industry-leading", "award-winning",
    "highly motivated", "results-driven", "passionate developer",
    "synergy", "leverage", "thought leader", "ninja", "guru", "rockstar",
    "высокомотивированный", "нацеленный на результат", "стрессоустойчивый",
    "командный игрок", "уникальное сочетание", "инновационные решения",
    "динамично развивающийся",
]

# Технологии, которые не сочетаются без объяснений
_INCOMPATIBLE_PAIRS = [
    ({"Django"}, {"FastAPI"}),     # редко в одном проекте
    ({"Flask"}, {"FastAPI"}),
    ({"MySQL"}, {"PostgreSQL"}),   # два реляционных DB в одном проекте — необычно
]


@dataclass
class RealismReport:
    career_realism: int = 100
    technical_realism: int = 100
    business_realism: int = 100
    organizational_realism: int = 100
    language_realism: int = 100
    issues: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        dims = [
            self.career_realism,
            self.technical_realism,
            self.business_realism,
            self.organizational_realism,
            self.language_realism,
        ]
        return round(sum(dims) / len(dims))


class RealismValidator:
    """Проверяет реалистичность карьерного профиля и текста резюме."""

    def validate(
        self,
        profile: CareerProfile,
        resume: ResumeDocument | None = None,
    ) -> RealismReport:
        report = RealismReport()

        self._check_career_realism(profile, report)
        self._check_technical_realism(profile, report)
        self._check_business_realism(profile, report)
        self._check_organizational_realism(profile, report)

        if resume:
            self._check_language_realism(resume, report)

        if report.issues:
            logger.info("RealismValidator: %d issues (score=%d)", len(report.issues), report.score)

        return report

    # ── Career ────────────────────────────────────────────────────────────────

    def _check_career_realism(self, profile: CareerProfile, report: RealismReport) -> None:
        candidate = profile.candidate
        penalty = 0

        # Слишком много опыта для возраста
        implied_start = candidate.age - candidate.total_experience_years
        if implied_start < 17:
            report.issues.append(
                f"Career: work implied to start at age {implied_start} — unrealistically young."
            )
            penalty += 15

        # Слишком быстрый карьерный рост
        if candidate.seniority == "Senior" and candidate.total_experience_years < 5:
            report.issues.append(
                f"Career: Senior with only {candidate.total_experience_years} years is unusual."
            )
            penalty += 10

        # Junior со стажем как Middle
        if candidate.seniority == "Junior" and candidate.total_experience_years > 4:
            report.issues.append(
                f"Career: Junior with {candidate.total_experience_years} years looks like Middle."
            )
            penalty += 8

        report.career_realism = max(50, 100 - penalty)

    # ── Technical ─────────────────────────────────────────────────────────────

    def _check_technical_realism(self, profile: CareerProfile, report: RealismReport) -> None:
        penalty = 0

        for role in profile.roles:
            techs = set(role.technologies)

            # Проверяем несовместимые пары
            for set_a, set_b in _INCOMPATIBLE_PAIRS:
                if set_a & techs and set_b & techs:
                    report.issues.append(
                        f"Technical: unusual tech mix {set_a | set_b} at {role.company.name}."
                    )
                    penalty += 5

            # Слишком большой стек для Junior
            if profile.candidate.seniority == "Junior" and len(techs) > 10:
                report.issues.append(
                    f"Technical: Junior with {len(techs)} technologies seems unlikely."
                )
                penalty += 5

            # Задачи ссылаются на технологии вне стека проекта
            for task in role.tasks:
                unknown_techs = [
                    t for t in task.technologies
                    if t not in techs and t not in ("Git", "Pytest", "unittest")
                ]
                if len(unknown_techs) > 2:
                    report.issues.append(
                        f"Technical: task references {unknown_techs} not in project stack at {role.company.name}."
                    )
                    penalty += 3

        report.technical_realism = max(50, 100 - penalty)

    # ── Business ──────────────────────────────────────────────────────────────

    def _check_business_realism(self, profile: CareerProfile, report: RealismReport) -> None:
        penalty = 0

        for role in profile.roles:
            # Маленькая компания с enterprise-масштабом
            if role.company.employees < 30 and "enterprise" in role.project.scale.lower():
                report.issues.append(
                    f"Business: {role.company.name} has {role.company.employees} employees "
                    f"but enterprise-scale project."
                )
                penalty += 7

            # Проект без пользователей
            if not role.project.target_users:
                report.issues.append(f"Business: project at {role.company.name} has no target users defined.")
                penalty += 3

        report.business_realism = max(50, 100 - penalty)

    # ── Organizational ────────────────────────────────────────────────────────

    def _check_organizational_realism(self, profile: CareerProfile, report: RealismReport) -> None:
        penalty = 0

        for role in profile.roles:
            team = role.team
            company = role.company

            # Команда больше компании
            if team.size > company.employees:
                report.issues.append(
                    f"Organizational: team ({team.size}) > company ({company.employees}) at {company.name}."
                )
                penalty += 10

            # Очень маленькая компания с большой командой
            if company.employees < 20 and team.size > 8:
                report.issues.append(
                    f"Organizational: {company.name} has {company.employees} employees "
                    f"but team of {team.size}."
                )
                penalty += 5

        report.organizational_realism = max(50, 100 - penalty)

    # ── Language ──────────────────────────────────────────────────────────────

    def _check_language_realism(self, resume: ResumeDocument, report: RealismReport) -> None:
        penalty = 0

        full_text = " ".join([
            resume.summary,
            *[b for exp in resume.experience for b in exp.bullets],
        ]).lower()

        # Hype-слова
        found_hype = [m for m in _HYPE_MARKERS if m in full_text]
        if found_hype:
            report.issues.append(f"Язык: обнаружены шаблонные клише: {found_hype}.")
            penalty += len(found_hype) * 4

        letters = re.findall(r"[A-Za-zА-Яа-яЁё]", full_text)
        cyrillic = re.findall(r"[А-Яа-яЁё]", full_text)
        if letters and len(cyrillic) / len(letters) < 0.45:
            report.issues.append(
                "Язык: основная проза резюме должна быть на русском языке."
            )
            penalty += 20

        # Все bullets начинаются с одного слова
        all_bullets = [b for exp in resume.experience for b in exp.bullets]
        if len(all_bullets) >= 4:
            first_words = [b.split()[0].lower() if b.split() else "" for b in all_bullets]
            most_common = max(set(first_words), key=first_words.count)
            count = first_words.count(most_common)
            if count >= len(all_bullets) * 0.6:
                report.issues.append(
                    f"Язык: {count}/{len(all_bullets)} достижений начинаются со слова "
                    f"«{most_common}» — формулировки однообразны."
                )
                penalty += 8

        # Слишком короткое summary
        if len(resume.summary.split()) < 15:
            report.issues.append("Язык: профессиональный профиль короче 15 слов.")
            penalty += 5

        report.language_realism = max(50, 100 - penalty)
