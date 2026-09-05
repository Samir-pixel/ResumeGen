"""Тесты RealismValidator."""
import pytest

from app.services.career_generator import CareerGenerator
from app.services.realism_validator import RealismValidator
from app.services.vacancy_analyzer import VacancyAnalyzer


@pytest.mark.asyncio
async def test_realism_validator_scores_normal_profile() -> None:
    """Нормальный Middle профиль должен иметь высокий realism score."""
    analysis = await VacancyAnalyzer().analyze(
        "Middle Python Backend Developer. FastAPI, PostgreSQL, Redis, Docker, Pytest. 3+ years."
    )
    profile = await CareerGenerator().generate(analysis, seed=42)
    report = RealismValidator().validate(profile)

    assert report.score >= 70, f"Realism score too low: {report.score}, issues: {report.issues}"
    assert report.career_realism >= 70
    assert report.technical_realism >= 70
    assert report.organizational_realism >= 70


@pytest.mark.asyncio
async def test_realism_validator_detects_hype_language() -> None:
    """Проверяет что hype-слова понижают language score."""
    from app.schemas import ResumeDocument

    analysis = await VacancyAnalyzer().analyze(
        "Middle Python Developer. FastAPI, PostgreSQL, Docker. 3+ years."
    )
    profile = await CareerGenerator().generate(analysis, seed=7)

    # Резюме с banned phrases
    bad_resume = ResumeDocument(
        header={"name": "Test User", "city": "Berlin", "email": "t@t.com", "phone": "+49"},
        target_position="Python Developer",
        summary="Highly motivated results-driven passionate developer with cutting-edge skills.",
        skills={"Backend": ["Python"]},
        experience=[],
        education=["BSc CS"],
        languages=["English"],
    )

    validator = RealismValidator()
    report = validator.validate(profile, bad_resume)

    assert report.language_realism < 90, \
        f"Expected lower language score due to hype markers, got {report.language_realism}"
    assert any("клише" in issue.lower() for issue in report.issues), \
        f"Expected language cliché issue, got: {report.issues}"
