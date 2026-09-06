"""Критик резюме — оценивает качество и соответствие вакансии."""
from __future__ import annotations

import logging
from pathlib import Path

from app.schemas import CareerProfile, CriticReport, ResumeDocument, VacancyAnalysis
from app.services.quality_scorer import ResumeQualityScorer

logger = logging.getLogger(__name__)

_CRITIC_PROMPT = Path("prompts/resume_critic/system.md")

_BANNED_PHRASES = [
    "highly motivated",
    "results-driven",
    "passionate developer",
    "cutting-edge",
    "dynamic professional",
    "unique combination",
    "synergy",
    "leverage",
    "out-of-the-box",
    "thought leader",
    "rock star developer",
    "высокомотивированный",
    "нацеленный на результат",
    "стрессоустойчивый",
    "командный игрок",
    "уникальное сочетание",
    "инновационные решения",
    "динамично развивающийся",
]


class ResumeCritic:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None

    async def review(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        resume: ResumeDocument,
    ) -> CriticReport:
        report = ResumeQualityScorer().score(analysis, profile, resume)
        if not self.llm:
            return report
        try:
            llm_report = await self._review_with_llm(analysis, profile, resume)
        except Exception:
            logger.exception("ResumeCritic: LLM review failed; using deterministic score")
            return report
        extra = [
            issue
            for issue in llm_report.issues
            if issue and issue not in report.issues
        ]
        report.issues.extend(extra[:8])
        return report

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _review_with_llm(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        resume: ResumeDocument,
    ) -> CriticReport:
        system = self._load_prompt()
        context = (
            f"Целевая должность: {analysis.title}\n"
            f"Обязательные навыки: {', '.join(analysis.required_skills)}\n"
            f"Уровень кандидата: {profile.candidate.seniority}\n\n"
            f"=== ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ ===\n{resume.summary}\n\n"
            f"=== НАВЫКИ ===\n{_format_skills(resume.skills)}\n\n"
            f"=== ОПЫТ ===\n{_format_bullets(resume.experience)}\n\n"
            f"=== ОБРАЗОВАНИЕ ===\n{'; '.join(resume.education)}\n"
        )
        logger.info("ResumeCritic: LLM review")
        return await self.llm.generate(system, context, CriticReport)

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _CRITIC_PROMPT.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = _DEFAULT_CRITIC_PROMPT
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _review_heuristic(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        resume: ResumeDocument,
    ) -> CriticReport:
        issues: list[str] = []

        body = " ".join(
            [resume.summary] + [b for item in resume.experience for b in item.bullets]
        ).lower()

        # Banned phrases
        for phrase in _BANNED_PHRASES:
            if phrase in body:
                issues.append(f"Обнаружено шаблонное клише: «{phrase}»")

        # Missing critical skills
        missing = [s for s in analysis.required_skills[:5] if s.lower() not in body]
        if missing:
            issues.append(f"В тексте резюме не отражены ключевые навыки: {', '.join(missing)}")

        # Career issues forwarded
        if profile.issues:
            issues.extend(profile.issues)

        # Summary length check
        if len(resume.summary.split()) < 20:
            issues.append("Профессиональный профиль слишком короткий: требуется 3–4 предложения.")

        # Bullet count check
        for exp in resume.experience:
            if len(exp.bullets) < 2:
                issues.append(f"Недостаточно достижений для роли в {exp.company}.")

        penalty = min(18, len(issues) * 3)
        base = 92
        score = max(60, base - penalty)

        return CriticReport(
            overall_score=score,
            relevance=max(78, score + 2),
            professionalism=max(78, score - 1),
            naturalness=max(76, score - 2),
            technical_realism=max(80, profile.quality_score),
            career_consistency=max(78, profile.quality_score - len(profile.issues) * 4),
            ats_quality=max(80, score),
            issues=issues,
        )


def _format_skills(skills: dict[str, list[str]]) -> str:
    return "\n".join(f"{group}: {', '.join(items)}" for group, items in skills.items())


def _format_bullets(experience: list) -> str:
    lines = []
    for exp in experience:
        lines.append(f"[{exp.company} — {exp.role}]")
        for b in exp.bullets:
            lines.append(f"  • {b}")
    return "\n".join(lines)


_DEFAULT_CRITIC_PROMPT = """Ты профессиональный редактор резюме технических специалистов.

Оцени русскоязычное резюме относительно вакансии и верни только JSON по схеме CriticReport.

Оцени каждое поле от 0 до 100. Проверяй релевантность, профессиональность,
естественность русского языка, технический реализм, карьерную связность и ATS-качество.
Снижай оценку за канцелярит, клише, смешение языков и одинаковое начало достижений.
Названия технологий и компаний на латинице не считай смешением языков.
"""
