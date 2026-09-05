"""Тесты анализатора вакансий."""
import pytest

from app.services.vacancy_analyzer import VacancyAnalyzer


@pytest.mark.asyncio
async def test_vacancy_analyzer_extracts_python_backend_requirements() -> None:
    vacancy = """
    Middle Python Backend Developer
    Build FastAPI services with PostgreSQL, Redis, Docker, SQLAlchemy and Pytest.
    Integrate external services and improve API reliability.
    3+ years of experience required.
    """

    analysis = await VacancyAnalyzer().analyze(vacancy)

    assert analysis.seniority == "Middle"
    assert analysis.title == "Python backend-разработчик"
    assert "Python" in analysis.required_skills
    assert "FastAPI" in analysis.required_skills
    assert "PostgreSQL" in analysis.required_skills
    assert len(analysis.responsibilities) >= 1


@pytest.mark.asyncio
async def test_vacancy_analyzer_detects_seniority() -> None:
    senior_vacancy = "Senior Python Backend Developer. Lead team, design architecture. 7+ years experience."
    junior_vacancy = "Junior Python Developer. 1+ years. Learning environment. Internship."

    senior = await VacancyAnalyzer().analyze(senior_vacancy)
    junior = await VacancyAnalyzer().analyze(junior_vacancy)

    assert senior.seniority == "Senior"
    assert junior.seniority == "Junior"


@pytest.mark.asyncio
async def test_vacancy_analyzer_detects_domain() -> None:
    fintech_vacancy = "Python Developer for payment platform. Work on transaction processing, billing, KYC."
    logistics_vacancy = "Backend Developer for shipment tracking and warehouse management system."

    fintech = await VacancyAnalyzer().analyze(fintech_vacancy)
    logistics = await VacancyAnalyzer().analyze(logistics_vacancy)

    assert fintech.domain == "FinTech"
    assert logistics.domain == "Logistics"


@pytest.mark.asyncio
async def test_vacancy_analyzer_handles_russian_vacancy() -> None:
    vacancy = """
    Старший Python backend-разработчик
    Проектировать API на FastAPI и оптимизировать запросы PostgreSQL.
    Разрабатывать фоновые задачи с Celery и Redis.
    Требуется от 6 лет коммерческого опыта.
    """

    analysis = await VacancyAnalyzer().analyze(vacancy)

    assert analysis.seniority == "Senior"
    assert analysis.required_experience == 6
    assert analysis.title == "Старший Python backend-разработчик"
    assert any("Проектировать" in item for item in analysis.responsibilities)
