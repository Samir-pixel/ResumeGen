"""Тесты валидатора консистентности."""
import pytest

from app.services.career_generator import CareerGenerator
from app.services.consistency_validator import ConsistencyValidator
from app.services.vacancy_analyzer import VacancyAnalyzer


@pytest.mark.asyncio
async def test_middle_profile_does_not_create_executive_role() -> None:
    """Middle разработчик не должен иметь executive-уровень."""
    analysis = await VacancyAnalyzer().analyze(
        "Middle Python Developer with FastAPI, PostgreSQL, Redis, Docker and Pytest. 3+ years."
    )

    profile = await CareerGenerator().generate(analysis, seed=42)
    issues = ConsistencyValidator().validate(profile)
    role_text = " ".join(role.role + " " + role.team.candidate_role for role in profile.roles)

    assert "CTO" not in role_text
    assert "VP Engineering" not in role_text


@pytest.mark.asyncio
async def test_junior_profile_has_limited_experience() -> None:
    """Junior профиль не должен иметь > 3 лет опыта."""
    analysis = await VacancyAnalyzer().analyze(
        "Junior Python Developer. 1+ year experience. Entry-level position."
    )

    profile = await CareerGenerator().generate(analysis, seed=7)

    assert profile.candidate.total_experience_years <= 3


@pytest.mark.asyncio
async def test_team_size_not_exceed_company() -> None:
    """Команда не должна быть больше компании."""
    analysis = await VacancyAnalyzer().analyze(
        "Middle Python Backend Developer, FastAPI, PostgreSQL, Redis, Docker. 3+ years."
    )

    profile = await CareerGenerator().generate(analysis, seed=100)
    issues = ConsistencyValidator().validate(profile)

    company_team_issues = [
        i for i in issues if "larger than company" in i
    ]
    assert not company_team_issues, f"Team/company size issues: {company_team_issues}"
