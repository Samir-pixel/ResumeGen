from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GenerationRunModel(Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    model: Mapped[str] = mapped_column(String(64), default="heuristic")
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1")
    vacancy_text: Mapped[str] = mapped_column(Text)
    vacancy_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    career_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resume_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    critic_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

