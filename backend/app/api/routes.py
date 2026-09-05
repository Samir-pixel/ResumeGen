"""API маршруты — создание генераций, статус, preview, PDF."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.repositories.file_repository import FileGenerationRepository
from app.schemas import (
    CandidateInfo,
    EducationEntry,
    GenerationRun,
    GenerationStatus,
    LanguageEntry,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


# ── Request / Response models ─────────────────────────────────────────────────

class GenerationRequest(BaseModel):
    vacancy_text: str = Field(min_length=20, description="Полный текст вакансии")
    template: str = Field(default="modern", description="Шаблон резюме: modern | ats | classic")
    # Личные данные — вводит пользователь. Если не заполнены — показывается placeholder.
    full_name: str = Field(default="", description="Имя и фамилия кандидата")
    city: str = Field(default="", description="Город проживания")
    phone: str = Field(default="", description="Телефон")
    telegram: str = Field(default="", description="Telegram: @username")
    email: str = Field(default="", description="Email (опционально)")
    education: list[EducationEntry] = Field(
        default_factory=list,
        description="Образование кандидата",
    )
    languages: list[LanguageEntry] = Field(
        default_factory=list,
        description="Языки и уровни владения",
    )


class GenerationCreatedResponse(BaseModel):
    generation_id: str
    status: str


# ── Dependency helpers ─────────────────────────────────────────────────────────

def _repo() -> FileGenerationRepository:
    settings = get_settings()
    return FileGenerationRepository(settings.generated_storage_dir)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generations", response_model=GenerationCreatedResponse, status_code=202)
async def create_generation(
    payload: GenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Создаёт задание генерации резюме.

    Немедленно возвращает generation_id.
    Генерация выполняется асинхронно (в Celery worker или как background task).
    """
    settings = get_settings()
    generation_id = str(uuid4())

    # Собираем личные данные кандидата
    candidate_info = CandidateInfo(
        full_name=payload.full_name.strip(),
        city=payload.city.strip(),
        phone=payload.phone.strip(),
        telegram=payload.telegram.strip(),
        email=payload.email.strip(),
        education=payload.education,
        languages=payload.languages,
    )

    # Создаём начальную запись
    run = GenerationRun(
        generation_id=generation_id,
        status=GenerationStatus.queued,
        vacancy=payload.vacancy_text,
        template=payload.template,
        candidate_info=candidate_info,
        started_at=datetime.now(UTC).replace(tzinfo=None),
    )
    repo = _repo()
    repo.save(run)

    # Запускаем через Celery если есть активные воркеры, иначе — inline background task
    use_celery = settings.app_env not in ("local", "test") and _has_celery_workers()
    if use_celery:
        _try_celery(generation_id, payload.vacancy_text, candidate_info, settings)
        logger.info("Generation queued via Celery: %s", generation_id)
    else:
        logger.info("Running generation inline (background task): %s", generation_id)
        background_tasks.add_task(_run_inline, generation_id, payload.vacancy_text, candidate_info)

    return GenerationCreatedResponse(generation_id=generation_id, status="queued")


@router.get("/generations/{generation_id}")
async def get_generation(generation_id: str):
    """Возвращает текущий статус и результат генерации."""
    run = _repo().get(generation_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return run.model_dump(mode="json")


@router.get("/resumes/{generation_id}/preview", response_class=HTMLResponse)
async def preview_resume(generation_id: str):
    """Возвращает HTML-превью резюме."""
    run = _repo().get(generation_id)
    if run is None or run.html_path is None or not Path(run.html_path).exists():
        raise HTTPException(status_code=404, detail="Preview not available yet")
    return Path(run.html_path).read_text(encoding="utf-8")


@router.get("/resumes/{generation_id}/pdf")
async def download_pdf(generation_id: str):
    """Возвращает готовый PDF-файл резюме."""
    run = _repo().get(generation_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    if run.status != GenerationStatus.completed:
        raise HTTPException(status_code=425, detail=f"PDF not ready yet (status: {run.status})")
    if run.pdf_path is None or not Path(run.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    pdf_path = Path(run.pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={"Content-Disposition": f'attachment; filename="{pdf_path.name}"'},
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _has_celery_workers() -> bool:
    """Проверяет, есть ли активные Celery воркеры (с таймаутом 0.5s)."""
    try:
        from app.workers.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=0.5)
        active = inspector.active()
        return bool(active)
    except Exception:
        return False


def _try_celery(generation_id: str, vacancy: str, candidate_info: CandidateInfo, settings) -> bool:
    """Отправляет задачу в Celery. Возвращает True если успешно."""
    try:
        from app.workers.tasks import run_generation_task
        run_generation_task.delay(generation_id, vacancy, candidate_info.model_dump())
        return True
    except Exception as exc:
        logger.warning("Celery недоступен: %s", exc)
        return False


async def _run_inline(
    generation_id: str, vacancy: str, candidate_info: CandidateInfo | None = None
) -> None:
    """Запускает пайплайн напрямую (когда Celery недоступен)."""
    from app.core.config import get_settings as _gs
    from app.repositories.file_repository import FileGenerationRepository as _Repo
    from app.services.generation_pipeline import GenerationPipeline

    settings = _gs()
    repo = _Repo(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repo)
    await pipeline.run(generation_id, vacancy, candidate_info=candidate_info)
