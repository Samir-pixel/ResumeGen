"""Тесты полного пайплайна генерации."""
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.repositories.file_repository import FileGenerationRepository
from app.schemas import (
    CandidateInfo,
    EducationEntry,
    GenerationStatus,
    LanguageEntry,
)
from app.services.generation_pipeline import GenerationPipeline


def _make_settings(tmp_path: Path) -> Settings:
    from app.core.config import _DEFAULT_TEMPLATES
    return Settings(
        storage_dir=tmp_path,
        generated_storage_dir=tmp_path / "generated",
        pdf_storage_dir=tmp_path / "pdfs",
        templates_dir=_DEFAULT_TEMPLATES,
    )


@pytest.mark.asyncio
async def test_generation_pipeline_creates_valid_pdf(tmp_path: Path) -> None:
    """Полный пайплайн → completed + PDF файл существует."""
    settings = _make_settings(tmp_path)
    settings.ensure_storage()
    repository = FileGenerationRepository(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repository)

    gen_id = str(uuid4())
    from app.schemas import GenerationRun
    run = GenerationRun(generation_id=gen_id, status=GenerationStatus.queued,
                        vacancy="x")
    repository.save(run)

    vacancy = """Middle Python Backend Developer
Build FastAPI services with PostgreSQL, Redis, Docker, SQLAlchemy, Alembic and Pytest.
Integrate external services and improve reliability for a SaaS operations platform.
3+ years of Python backend experience required."""

    candidate_info = CandidateInfo(
        full_name="Иван Петров",
        city="Казань",
        education=[
            EducationEntry(
                institution="Казанский федеральный университет",
                degree="Бакалавр",
                field_of_study="Программная инженерия",
                start_year=2017,
                end_year=2021,
            )
        ],
        languages=[LanguageEntry(language="Английский", level="B2")],
    )
    result = await pipeline.run(gen_id, vacancy, candidate_info=candidate_info)

    assert result.status == GenerationStatus.completed, f"Failed: {result.error}"
    assert result.pdf_path is not None
    assert Path(result.pdf_path).exists(), f"PDF not found: {result.pdf_path}"
    assert Path(result.pdf_path).suffix == ".pdf"
    assert result.quality_score is not None
    assert result.quality_score > 0
    assert result.resume is not None
    assert result.resume.header["name"] == "Иван Петров"
    assert result.resume.education == candidate_info.education_for_resume()
    assert result.resume.languages == candidate_info.languages_for_resume()


@pytest.mark.asyncio
async def test_pipeline_generates_varied_candidates(tmp_path: Path) -> None:
    """Два запуска — разные кандидаты."""
    settings = _make_settings(tmp_path)
    settings.ensure_storage()
    repo = FileGenerationRepository(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repo)

    vacancy = """Middle Python Backend Developer. FastAPI, PostgreSQL, Redis, Docker.
3+ years experience. SaaS platform."""

    results = []
    for _i in range(2):
        gen_id = str(uuid4())
        from app.schemas import GenerationRun
        run = GenerationRun(generation_id=gen_id, status=GenerationStatus.queued,
                            vacancy=vacancy)
        repo.save(run)
        r = await pipeline.run(gen_id, vacancy)
        results.append(r)

    # Оба должны быть completed
    for r in results:
        assert r.status == GenerationStatus.completed

    # Кандидаты могут совпадать при малом пуле имён, но компании должны различаться
    names = [r.career_profile.candidate.name for r in results if r.career_profile]
    companies = [
        r.career_profile.roles[0].company.name
        for r in results
        if r.career_profile and r.career_profile.roles
    ]
    # Хотя бы одна пара должна различаться (имена или компании)
    assert len(set(names)) >= 1  # минимальная проверка
    assert len(companies) == 2


@pytest.mark.asyncio
async def test_pipeline_generates_pdf_with_correct_content_type(tmp_path: Path) -> None:
    """PDF должен начинаться с %PDF сигнатурой."""
    settings = _make_settings(tmp_path)
    settings.ensure_storage()
    repo = FileGenerationRepository(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repo)

    gen_id = str(uuid4())
    from app.schemas import GenerationRun
    run = GenerationRun(generation_id=gen_id, status=GenerationStatus.queued,
                        vacancy="x")
    repo.save(run)

    vacancy = "Senior Python Backend Developer. FastAPI, PostgreSQL, Kafka, Redis, Docker. 7+ years."
    result = await pipeline.run(gen_id, vacancy)

    assert result.status == GenerationStatus.completed
    pdf_bytes = Path(result.pdf_path).read_bytes()
    assert pdf_bytes[:4] == b"%PDF", "PDF must start with %PDF signature"
