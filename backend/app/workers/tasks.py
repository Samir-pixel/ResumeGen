"""Celery задачи для асинхронной генерации резюме."""
from __future__ import annotations

import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="resume_generator.run_generation",
    bind=True,
    max_retries=0,
    acks_late=True,
    soft_time_limit=300,
    time_limit=360,
)
def run_generation_task(self, generation_id: str, vacancy: str) -> dict:
    """Запускает полный пайплайн генерации резюме в Celery worker."""
    logger.info("Task started: generation_id=%s", generation_id)
    try:
        result = asyncio.run(_run_pipeline(generation_id, vacancy))

        logger.info(
            "Task completed: generation_id=%s status=%s",
            generation_id,
            result.get("status"),
        )
        return result
    except Exception as exc:
        logger.exception("Task failed: generation_id=%s error=%s", generation_id, exc)
        raise


async def _run_pipeline(generation_id: str, vacancy: str) -> dict:
    from app.core.config import get_settings
    from app.repositories.file_repository import FileGenerationRepository
    from app.services.generation_pipeline import GenerationPipeline

    settings = get_settings()
    repository = FileGenerationRepository(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repository)

    run = await pipeline.run(generation_id, vacancy)
    return run.model_dump(mode="json")
