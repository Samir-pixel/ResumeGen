from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

Seniority = Literal["Junior", "Middle", "Senior"]


class LanguageLevel(StrEnum):
    native = "native"
    c2 = "C2"
    c1 = "C1"
    b2 = "B2"
    b1 = "B1"
    a2 = "A2"
    a1 = "A1"


_LANGUAGE_LEVEL_LABELS: dict[LanguageLevel, str] = {
    LanguageLevel.native: "Родной",
    LanguageLevel.c2: "C2 — свободное владение",
    LanguageLevel.c1: "C1 — продвинутый",
    LanguageLevel.b2: "B2 — выше среднего",
    LanguageLevel.b1: "B1 — средний",
    LanguageLevel.a2: "A2 — базовый",
    LanguageLevel.a1: "A1 — начальный",
}


class EducationEntry(BaseModel):
    institution: str = Field(min_length=2, max_length=160)
    degree: str = Field(min_length=2, max_length=80)
    field_of_study: str = Field(default="", max_length=120)
    start_year: int = Field(ge=1940, le=2100)
    end_year: int | None = Field(default=None, ge=1940, le=2100)

    @model_validator(mode="after")
    def validate_years(self) -> "EducationEntry":
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("Год окончания не может быть раньше года начала")
        return self

    def to_resume_text(self) -> str:
        qualification = ", ".join(
            part for part in (self.degree.strip(), self.field_of_study.strip()) if part
        )
        period = (
            f"{self.start_year}–{self.end_year}"
            if self.end_year is not None
            else f"{self.start_year}–н. в."
        )
        return f"{qualification} — {self.institution.strip()}, {period}"


class LanguageEntry(BaseModel):
    language: str = Field(min_length=2, max_length=60)
    level: LanguageLevel

    def to_resume_text(self) -> str:
        return f"{self.language.strip()} — {_LANGUAGE_LEVEL_LABELS[self.level]}"


class GenerationStatus(StrEnum):
    queued = "queued"
    analyzing_vacancy = "analyzing_vacancy"
    generating_candidate = "generating_candidate"
    generating_companies = "generating_companies"
    generating_projects = "generating_projects"
    generating_experience = "generating_experience"
    validating = "validating"
    writing_resume = "writing_resume"
    criticizing = "criticizing"
    rendering_pdf = "rendering_pdf"
    validating_pdf = "validating_pdf"
    completed = "completed"
    failed = "failed"


class VacancyAnalysis(BaseModel):
    title: str
    seniority: Seniority
    required_experience: int = Field(ge=0, le=20)
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    domain: str
    language: str = "en"
    is_nda_domain: bool = False
    company_context: str
    priority_requirements: list[str]


class CandidateInfo(BaseModel):
    """Личные данные кандидата, которые вводит пользователь вручную.
    Все поля опциональные — если не заполнены, в PDF будет placeholder.
    """
    full_name: str = ""          # Имя Фамилия
    city: str = ""               # Город проживания
    phone: str = ""              # Телефон
    telegram: str = ""           # @username или t.me/username
    email: str = ""              # Email (опционально)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)

    def education_for_resume(self) -> list[str]:
        return [entry.to_resume_text() for entry in self.education]

    def languages_for_resume(self) -> list[str]:
        return [entry.to_resume_text() for entry in self.languages]


class Candidate(BaseModel):
    name: str
    age: int = Field(ge=18, le=65)
    city: str
    title: str
    seniority: Seniority
    total_experience_years: int = Field(ge=0, le=35)
    education: list[str]
    languages: list[str]
    email: str
    phone: str
    telegram: str = ""


class Company(BaseModel):
    name: str
    industry: str
    sector: str
    employees: int = Field(ge=5, le=100000)
    location: str
    business_description: str


class Team(BaseModel):
    size: int = Field(ge=2, le=80)
    roles: list[str]
    structure: str
    candidate_role: str
    collaboration: str


class Project(BaseModel):
    name: str
    description: str
    business_purpose: str
    target_users: str
    scale: str
    modules: list[str]
    architecture: str
    integrations: list[str]
    databases: list[str]
    infrastructure: list[str]
    technologies: list[str]


class ExperienceTask(BaseModel):
    context: str
    problem: str
    task: str
    actions: list[str]
    technologies: list[str]
    reason: str
    constraints: list[str]
    result: str
    complexity: int = Field(ge=1, le=5)
    business_impact: str
    technical_impact: str


class QualityScores(BaseModel):
    technical_realism: int = Field(ge=0, le=100)
    business_realism: int = Field(ge=0, le=100)
    career_consistency: int = Field(ge=0, le=100)
    seniority_consistency: int = Field(ge=0, le=100)
    language_quality: int = Field(ge=0, le=100)

    @property
    def quality_score(self) -> int:
        values = [
            self.technical_realism,
            self.business_realism,
            self.career_consistency,
            self.seniority_consistency,
            self.language_quality,
        ]
        return round(sum(values) / len(values))


class RoleExperience(BaseModel):
    company: Company
    start_date: str
    end_date: str
    role: str
    project: Project
    team: Team
    tasks: list[ExperienceTask]
    technologies: list[str]
    quality: QualityScores


class CareerProfile(BaseModel):
    candidate: Candidate
    roles: list[RoleExperience]
    quality_score: int
    issues: list[str] = Field(default_factory=list)


class ResumeExperience(BaseModel):
    company: str
    sector: str
    location: str
    dates: str
    role: str
    company_description: str
    project_description: str
    team: str
    bullets: list[str]
    technologies: list[str]


class ResumeDocument(BaseModel):
    header: dict[str, str]
    target_position: str
    summary: str
    skills: dict[str, list[str]]
    experience: list[ResumeExperience]
    education: list[str]
    languages: list[str]


class CriticReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    relevance: int = Field(ge=0, le=100)
    professionalism: int = Field(ge=0, le=100)
    naturalness: int = Field(ge=0, le=100)
    technical_realism: int = Field(ge=0, le=100)
    career_consistency: int = Field(ge=0, le=100)
    ats_quality: int = Field(ge=0, le=100)
    issues: list[str]


class GenerationRun(BaseModel):
    generation_id: str = Field(default_factory=lambda: str(uuid4()))
    status: GenerationStatus = GenerationStatus.queued
    model: str = "heuristic"
    prompt_version: str = "v1"
    template: str = "modern"
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    completed_at: datetime | None = None
    quality_score: int | None = None
    vacancy: str
    candidate_info: CandidateInfo = Field(default_factory=CandidateInfo)
    vacancy_analysis: VacancyAnalysis | None = None
    career_profile: CareerProfile | None = None
    resume: ResumeDocument | None = None
    critic: CriticReport | None = None
    html_path: Path | None = None
    pdf_path: Path | None = None
    pdf_url: str | None = None
    resume_id: str | None = None
    error: str | None = None
    stages: list[dict[str, str]] = Field(default_factory=list)
