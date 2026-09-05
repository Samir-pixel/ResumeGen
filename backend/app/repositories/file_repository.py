from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import TypeAdapter

from app.schemas import GenerationRun, GenerationStatus


class FileGenerationRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.adapter = TypeAdapter(GenerationRun)

    def save(self, run: GenerationRun) -> GenerationRun:
        path = self._path(run.generation_id)
        data = run.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return run

    def get(self, generation_id: str) -> GenerationRun | None:
        path = self._path(generation_id)
        if not path.exists():
            return None
        return self.adapter.validate_json(path.read_text(encoding="utf-8"))

    def mark_failed(self, run: GenerationRun, error: str) -> GenerationRun:
        run.status = GenerationStatus.failed
        run.error = error
        run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.save(run)

    def _path(self, generation_id: str) -> Path:
        return self.directory / f"{generation_id}.json"

