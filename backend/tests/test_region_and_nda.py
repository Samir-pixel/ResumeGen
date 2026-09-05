"""Регион работодателей и правило NDA для русскоязычных вакансий."""
from __future__ import annotations

import random

import pytest

from app.schemas import CandidateInfo
from app.services.career_generator import CareerGenerator
from app.services.company_generator import CompanyGenerator
from app.services.knowledge_base_ru import NDA_COMPANY_NAME, RU_LOCATIONS
from app.services.vacancy_analyzer import VacancyAnalyzer

KAZAN_VACANCY = """
Middle Python Developer (Python): Разработка платформы маркетинговых данных
и сервиса интерактивной телефонии. Локация: офис в Казани или удалённо по ТК РФ.
Разрабатывать платформу маркетинговых данных, интеграции с аналитическими сервисами
и пайплайны сбора данных. Требуется от 3 лет коммерческой разработки на Python.
"""


@pytest.mark.asyncio
async def test_kazan_vacancy_is_russian_and_not_nda() -> None:
    analysis = await VacancyAnalyzer().analyze(KAZAN_VACANCY)

    assert analysis.language == "ru"
    assert analysis.domain in {"AdTech", "Telecom"}
    assert analysis.is_nda_domain is False
    assert analysis.seniority == "Middle"


@pytest.mark.asyncio
async def test_russian_fintech_vacancy_hides_employers_as_nda() -> None:
    vacancy = (
        "Ищем Python-разработчика в финтех-компанию. "
        "Платежи, скоринг и обработка транзакций. Опыт от 3 лет."
    )
    analysis = await VacancyAnalyzer().analyze(vacancy)

    assert analysis.language == "ru"
    assert analysis.domain == "FinTech"
    assert analysis.is_nda_domain is True


@pytest.mark.asyncio
async def test_explicit_nda_hides_employer_even_outside_fintech() -> None:
    vacancy = (
        "Python backend-разработчик. Компания работает под NDA. "
        "Нужен опыт FastAPI и PostgreSQL, от 3 лет."
    )
    analysis = await VacancyAnalyzer().analyze(vacancy)

    assert analysis.is_nda_domain is True


@pytest.mark.asyncio
async def test_english_fintech_keeps_real_company_names() -> None:
    vacancy = (
        "Python developer for a payment platform. Work on transactions, "
        "billing and KYC. 3+ years of experience."
    )
    analysis = await VacancyAnalyzer().analyze(vacancy)

    assert analysis.language == "en"
    assert analysis.domain == "FinTech"
    assert analysis.is_nda_domain is False


def test_russian_product_companies_stay_in_ru_kz_by() -> None:
    generator = CompanyGenerator()
    rng = random.Random(11)
    allowed_cities = {location.split(",")[0] for location in RU_LOCATIONS}

    for index in range(8):
        company = generator._create_product_company("AdTech", index, rng, "ru")
        city = company.location.split(",")[0]
        assert city in allowed_cities
        assert company.name != NDA_COMPANY_NAME


def test_nda_company_uses_fixed_name() -> None:
    company = CompanyGenerator()._create_nda_company("FinTech", 0, random.Random(1))

    assert company.name == NDA_COMPANY_NAME
    assert company.location == "Удалённо"
    assert "NDA" in company.sector


@pytest.mark.asyncio
async def test_kazan_career_uses_regional_or_nda_names() -> None:
    analysis = await VacancyAnalyzer().analyze(KAZAN_VACANCY)
    profile = await CareerGenerator().generate(
        analysis,
        seed=21,
        candidate_info=CandidateInfo(full_name="Иван Петров", city="Казань"),
    )

    allowed_suffixes = ("Россия", "Казахстан", "Беларусь")
    for role in profile.roles:
        if analysis.is_nda_domain:
            assert role.company.name == NDA_COMPANY_NAME
        else:
            assert role.company.name != NDA_COMPANY_NAME
            assert role.company.location.endswith(allowed_suffixes)
