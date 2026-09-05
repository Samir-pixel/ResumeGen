"""Валидатор консистентности карьерного профиля."""
from __future__ import annotations

import logging
from datetime import date

from app.schemas import CareerProfile

logger = logging.getLogger(__name__)

_EXECUTIVE_TERMS = [
    "CTO", "VP Engineering", "Head of Engineering", "VP of Technology",
    "Director of Engineering", "Chief Technical Officer",
]

_JUNIOR_FORBIDDEN_COMPLEXITY = 4  # complexity >= этого значения — ошибка для Junior


class ConsistencyValidator:
    def validate(self, profile: CareerProfile) -> list[str]:
        issues: list[str] = []
        candidate = profile.candidate
        current_year = date.today().year

        # ── Timeline ──────────────────────────────────────────────────────────
        if candidate.age < 21 and candidate.total_experience_years > 3:
            issues.append(
                f"Timeline inconsistency: age {candidate.age} is too low "
                f"for {candidate.total_experience_years} years of experience."
            )

        if candidate.age - candidate.total_experience_years < 18:
            issues.append(
                f"Timeline inconsistency: work would have started at age "
                f"{candidate.age - candidate.total_experience_years}."
            )

        # ── Seniority ─────────────────────────────────────────────────────────
        if candidate.seniority == "Junior" and candidate.total_experience_years > 3:
            issues.append(
                f"Seniority inconsistency: Junior profile has {candidate.total_experience_years} "
                "years of experience (max expected: 3)."
            )

        if candidate.seniority == "Middle":
            combined_text = " ".join(
                role.role + " " + role.team.candidate_role for role in profile.roles
            )
            for term in _EXECUTIVE_TERMS:
                if term in combined_text:
                    issues.append(
                        f"Seniority inconsistency: Middle profile contains executive role '{term}'."
                    )

        # ── Company vs Team ───────────────────────────────────────────────────
        for role in profile.roles:
            if role.company.employees < role.team.size:
                issues.append(
                    f"Company inconsistency: team size ({role.team.size}) is larger than "
                    f"company headcount ({role.company.employees}) at {role.company.name}."
                )

        # ── Task complexity ───────────────────────────────────────────────────
        if candidate.seniority == "Junior":
            for role in profile.roles:
                high_complexity = [
                    t for t in role.tasks if t.complexity >= _JUNIOR_FORBIDDEN_COMPLEXITY
                ]
                if high_complexity:
                    issues.append(
                        f"Complexity inconsistency: Junior profile has tasks with complexity "
                        f">= {_JUNIOR_FORBIDDEN_COMPLEXITY} at {role.company.name}."
                    )

        # ── Date continuity ───────────────────────────────────────────────────
        try:
            self._check_date_gaps(profile, issues)
        except Exception as exc:
            logger.debug("Date gap check skipped: %s", exc)

        if issues:
            logger.warning("ConsistencyValidator: обнаружено %d проблем", len(issues))

        return issues

    def _check_date_gaps(self, profile: CareerProfile, issues: list[str]) -> None:
        """Проверяет, что даты ролей не пересекаются."""
        parsed = []
        for role in profile.roles:
            start = _parse_year(role.start_date)
            end = _parse_year(role.end_date)
            if start and end:
                parsed.append((start, end, role.company.name))

        parsed.sort(key=lambda x: x[0])
        for i in range(len(parsed) - 1):
            end_a = parsed[i][1]
            start_b = parsed[i + 1][0]
            if start_b < end_a - 1:  # допускаем перекрытие на 1 год (смена работы)
                issues.append(
                    f"Date inconsistency: overlap between {parsed[i][2]} "
                    f"(ends {end_a}) and {parsed[i+1][2]} (starts {start_b})."
                )


def _parse_year(date_str: str) -> int | None:
    if date_str == "Present":
        return date.today().year
    try:
        return int(date_str.split("-")[0])
    except (ValueError, IndexError):
        return None
