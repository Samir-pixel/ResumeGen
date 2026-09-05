from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import Settings
from app.repositories.file_repository import FileGenerationRepository
from app.schemas import GenerationStatus
from app.services.generation_pipeline import GenerationPipeline


VACANCY = """
Middle Python Backend Developer

We need a backend developer for a SaaS operations platform. The role includes developing
FastAPI services, working with PostgreSQL, Redis, Docker, SQLAlchemy, Alembic and Pytest,
integrating external services, improving reliability and supporting production releases.
Kafka or Celery experience is a plus.
"""


async def main() -> int:
    settings = Settings(
        storage_dir=ROOT / "storage",
        generated_storage_dir=ROOT / "storage" / "generated",
        pdf_storage_dir=ROOT / "storage" / "pdfs",
        templates_dir=ROOT / "templates",
    )
    settings.ensure_storage()
    repository = FileGenerationRepository(settings.generated_storage_dir)
    pipeline = GenerationPipeline(settings, repository)
    run = await pipeline.run(VACANCY)
    if run.status != GenerationStatus.completed or run.pdf_path is None:
        print(f"FAILED: {run.error}")
        return 1
    print(f"generation_id={run.generation_id}")
    print(f"quality_score={run.quality_score}")
    print(f"pdf_path={run.pdf_path}")
    print(f"html_path={run.html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

