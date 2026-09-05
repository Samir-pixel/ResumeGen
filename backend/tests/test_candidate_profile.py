from pathlib import Path

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from app.schemas import (
    CandidateInfo,
    EducationEntry,
    LanguageEntry,
    ResumeDocument,
)
from app.services.career_generator import CareerGenerator
from app.services.pdf_renderer import PdfRenderer
from app.services.resume_writer import ResumeWriter
from app.services.vacancy_analyzer import VacancyAnalyzer


def _candidate_info() -> CandidateInfo:
    return CandidateInfo(
        full_name="Иван Петров",
        city="Казань",
        phone="+7 999 000-00-00",
        email="ivan@example.com",
        education=[
            EducationEntry(
                institution="Казанский федеральный университет",
                degree="Бакалавр",
                field_of_study="Программная инженерия",
                start_year=2017,
                end_year=2021,
            )
        ],
        languages=[
            LanguageEntry(language="Русский", level="native"),
            LanguageEntry(language="Английский", level="B2"),
        ],
    )


def test_structured_profile_formats_for_resume() -> None:
    info = _candidate_info()

    assert info.education_for_resume() == [
        "Бакалавр, Программная инженерия — Казанский федеральный университет, 2017–2021"
    ]
    assert info.languages_for_resume() == [
        "Русский — Родной",
        "Английский — B2 — выше среднего",
    ]


def test_education_rejects_reversed_years() -> None:
    with pytest.raises(ValidationError):
        EducationEntry(
            institution="Университет",
            degree="Бакалавр",
            start_year=2022,
            end_year=2018,
        )


@pytest.mark.asyncio
async def test_user_profile_data_survives_llm_resume_write() -> None:
    analysis = await VacancyAnalyzer().analyze(
        "Middle Python backend-разработчик. Разрабатывать FastAPI API и PostgreSQL. "
        "Требуется опыт от 3 лет."
    )
    info = _candidate_info()
    profile = await CareerGenerator().generate(analysis, seed=42, candidate_info=info)

    class FakeLlm:
        async def generate(self, system: str, user: str, response_model):
            return ResumeDocument(
                header={"name": "Выдуманное имя"},
                target_position=analysis.title,
                summary=(
                    "Backend-разработчик с опытом проектирования надёжных сервисов. "
                    "Работает с Python, FastAPI и PostgreSQL."
                ),
                skills={"Backend-разработка": ["Python", "FastAPI"]},
                experience=[],
                education=["Выдуманное образование"],
                languages=["Выдуманный язык"],
            )

    resume = await ResumeWriter(llm=FakeLlm()).write(analysis, profile, info)

    assert resume.header["name"] == "Иван Петров"
    assert resume.header["city"] == "Казань"
    assert resume.education == info.education_for_resume()
    assert resume.languages == info.languages_for_resume()


@pytest.mark.asyncio
async def test_mixed_language_llm_output_gets_localized() -> None:
    analysis = await VacancyAnalyzer().analyze(
        "Python backend-разработчик. Разрабатывать FastAPI API и PostgreSQL. "
        "Требуется опыт от 3 лет."
    )
    info = _candidate_info()
    profile = await CareerGenerator().generate(analysis, seed=10, candidate_info=info)

    class LocalizingLlm:
        calls = 0

        async def generate(self, system: str, user: str, response_model):
            self.calls += 1
            russian = self.calls > 1
            return ResumeDocument(
                header={"name": "Неверное имя"},
                target_position=analysis.title,
                summary=(
                    "Разрабатывает надёжные серверные приложения, проектирует API "
                    "и оптимизирует запросы к базам данных."
                    if russian
                    else "Experienced backend engineer building scalable services and integrations."
                ),
                skills={
                    "Backend-разработка" if russian else "Backend": ["Python", "FastAPI"]
                },
                experience=[],
                education=[],
                languages=[],
            )

    llm = LocalizingLlm()
    resume = await ResumeWriter(llm=llm).write(analysis, profile, info)

    assert llm.calls == 2
    assert "Разрабатывает" in resume.summary
    assert resume.header["name"] == info.full_name
    assert resume.education == info.education_for_resume()


@pytest.mark.asyncio
async def test_heuristic_resume_localizes_role_titles() -> None:
    analysis = await VacancyAnalyzer().analyze(
        "Python backend-разработчик. Разрабатывать FastAPI API и PostgreSQL. "
        "Требуется опыт от 3 лет."
    )
    profile = await CareerGenerator().generate(analysis, seed=7, candidate_info=_candidate_info())

    resume = await ResumeWriter().write(analysis, profile, _candidate_info())

    assert resume.experience
    assert all("Developer" not in item.role for item in resume.experience)
    assert all("Engineer" not in item.role for item in resume.experience)


def test_reportlab_fallback_preserves_cyrillic(tmp_path: Path) -> None:
    resume = ResumeDocument(
        header={"name": "Иван Петров", "city": "Казань"},
        target_position="Python backend-разработчик",
        summary="Разрабатывает надёжные серверные приложения и интеграции.",
        skills={"Backend-разработка": ["Python", "FastAPI"]},
        experience=[],
        education=["Бакалавр — Казанский федеральный университет, 2021"],
        languages=["Русский — Родной"],
    )
    output = tmp_path / "russian-fallback.pdf"

    PdfRenderer()._render_with_reportlab(resume, output)
    text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)

    assert "Иван Петров" in text
    assert "Профессиональный профиль" in text
    assert "Образование" in text
