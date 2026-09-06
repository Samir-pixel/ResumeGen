"""Детерминированная оценка резюме. Цифры считает код, не языковая модель."""
from __future__ import annotations

import re
from collections import Counter

from app.schemas import CareerProfile, CriticReport, ResumeDocument, VacancyAnalysis

WEIGHTS = {
    "relevance": 0.35,
    "professionalism": 0.20,
    "naturalness": 0.15,
    "technical_realism": 0.15,
    "career_consistency": 0.10,
    "ats_quality": 0.05,
}

PASS_THRESHOLD = 70

_CLICHES = (
    "высокомотивированный",
    "нацеленный на результат",
    "стрессоустойчивый",
    "командный игрок",
    "уникальное сочетание",
    "инновационные решения",
    "динамично развивающийся",
    "ориентированный на результат",
    "highly motivated",
    "results-driven",
    "passionate developer",
    "cutting-edge",
    "thought leader",
)

_GENERIC_BULLETS = (
    "работал над различными",
    "участвовал в разработке",
    "выполнял поставленные задачи",
    "занимался различными",
    "осуществлял деятельность",
    "производил реализацию",
)


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _body(resume: ResumeDocument) -> str:
    parts = [resume.summary, resume.target_position]
    for group, items in resume.skills.items():
        parts.append(group)
        parts.extend(items)
    for item in resume.experience:
        parts.extend(
            [
                item.company,
                item.role,
                item.company_description,
                item.project_description,
                item.team,
                *item.bullets,
                *item.technologies,
            ]
        )
    return " ".join(part for part in parts if part)


def _russian_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text)
    cyrillic = re.findall(r"[А-Яа-яЁё]", text)
    if not letters:
        return 0.0
    return len(cyrillic) / len(letters)


def _contains_skill(text: str, skill: str) -> bool:
    return skill.lower() in text.lower()


class ResumeQualityScorer:
    """Жёсткая 100-балльная рубрика. Итог = взвешенное среднее шести осей."""

    def score(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        resume: ResumeDocument,
    ) -> CriticReport:
        issues: list[str] = []
        hard_fails: list[str] = []
        body = _body(resume)
        body_lower = body.lower()

        relevance = self._relevance(analysis, resume, body_lower, issues, hard_fails)
        professionalism = self._professionalism(resume, body_lower, issues, hard_fails)
        naturalness = self._naturalness(resume, issues, hard_fails)
        technical = self._technical(analysis, profile, resume, body_lower, issues)
        career = self._career(profile, resume, issues)
        ats = self._ats(analysis, resume, body_lower, issues)

        overall = round(
            relevance * WEIGHTS["relevance"]
            + professionalism * WEIGHTS["professionalism"]
            + naturalness * WEIGHTS["naturalness"]
            + technical * WEIGHTS["technical_realism"]
            + career * WEIGHTS["career_consistency"]
            + ats * WEIGHTS["ats_quality"]
        )
        if hard_fails:
            overall = min(overall, PASS_THRESHOLD - 1)
            issues = [f"[блок] {item}" for item in hard_fails] + issues

        return CriticReport(
            overall_score=_clamp(overall),
            relevance=_clamp(relevance),
            professionalism=_clamp(professionalism),
            naturalness=_clamp(naturalness),
            technical_realism=_clamp(technical),
            career_consistency=_clamp(career),
            ats_quality=_clamp(ats),
            issues=issues,
        )

    def should_regenerate_career(self, report: CriticReport) -> bool:
        return report.relevance < 60 or report.career_consistency < 60

    def _relevance(
        self,
        analysis: VacancyAnalysis,
        resume: ResumeDocument,
        body_lower: str,
        issues: list[str],
        hard_fails: list[str],
    ) -> int:
        score = 100
        required = analysis.required_skills[:6]
        missing = [skill for skill in required if not _contains_skill(body_lower, skill)]
        if missing:
            score -= 12 * len(missing)
            issues.append(
                f"В резюме не подтверждены обязательные навыки: {', '.join(missing)}."
            )
        if len(missing) > 3:
            hard_fails.append(
                "Слишком много обязательных навыков вакансии отсутствуют в резюме."
            )
        if not resume.experience:
            score -= 40
            hard_fails.append("В резюме нет блока опыта работы.")
        if not resume.target_position.strip():
            score -= 10
            issues.append("Не указана целевая должность.")
        if analysis.title and analysis.title.lower() not in (
            resume.target_position.lower() + " " + resume.summary.lower()
        ):
            # Title may be localized; only light penalty
            score -= 4
        return score

    def _professionalism(
        self,
        resume: ResumeDocument,
        body_lower: str,
        issues: list[str],
        hard_fails: list[str],
    ) -> int:
        score = 100
        found_cliches = [phrase for phrase in _CLICHES if phrase in body_lower]
        if found_cliches:
            score -= min(40, 10 * len(found_cliches))
            issues.append(
                "Шаблонные клише: "
                + ", ".join(f"«{phrase}»" for phrase in found_cliches[:4])
                + "."
            )
        if len(found_cliches) >= 2:
            hard_fails.append(
                "Текст содержит несколько HR-клише и не проходит профессиональную проверку."
            )
        words = resume.summary.split()
        if len(words) < 12:
            score -= 25
            issues.append("Профессиональный профиль короче 12 слов.")
        elif len(words) < 20:
            score -= 12
            issues.append("Профессиональный профиль слишком короткий: нужно 3–4 предложения.")
        elif len(words) > 120:
            score -= 8
            issues.append("Профессиональный профиль слишком длинный для шапки резюме.")

        for item in resume.experience:
            if len(item.bullets) < 2:
                score -= 15
                issues.append(f"У роли в {item.company} меньше двух достижений.")
            elif len(item.bullets) < 3:
                score -= 8
                issues.append(f"У роли в {item.company} мало достижений: нужно 3–5 пунктов.")
            generic = [
                bullet
                for bullet in item.bullets
                if any(marker in bullet.lower() for marker in _GENERIC_BULLETS)
            ]
            if generic:
                score -= 5 * len(generic)
                issues.append(
                    f"В {item.company} есть слишком общие формулировки без технологии и результата."
                )
        return score

    def _naturalness(
        self,
        resume: ResumeDocument,
        issues: list[str],
        hard_fails: list[str],
    ) -> int:
        score = 100
        prose = " ".join(
            [resume.summary]
            + [item.company_description for item in resume.experience]
            + [item.project_description for item in resume.experience]
            + [bullet for item in resume.experience for bullet in item.bullets]
        )
        ratio = _russian_ratio(prose)
        if ratio < 0.45:
            score -= 35
            hard_fails.append(
                f"Основная проза не на русском языке (доля кириллицы {ratio:.0%})."
            )
        elif ratio < 0.62:
            score -= 18
            issues.append("В прозе слишком много английских предложений.")

        for item in resume.experience:
            starters = [
                re.split(r"\s+", bullet.strip(), maxsplit=1)[0].lower()
                for bullet in item.bullets
                if bullet.strip()
            ]
            if len(starters) < 3:
                continue
            top_word, count = Counter(starters).most_common(1)[0]
            if count >= 3:
                score -= 12
                issues.append(
                    f"В {item.company} {count} пунктов начинаются с «{top_word}» — разнообразите глаголы."
                )
        return score

    def _technical(
        self,
        analysis: VacancyAnalysis,
        profile: CareerProfile,
        resume: ResumeDocument,
        body_lower: str,
        issues: list[str],
    ) -> int:
        score = 92
        if profile.candidate.seniority == "Junior" and re.search(
            r"спроектировал(а)? всю|руководил(а)? командой|архитектуру платформы с нуля",
            body_lower,
        ):
            score -= 12
            issues.append("Формулировки Junior завышают ответственность до уровня Senior.")
        if profile.candidate.seniority == "Middle" and re.search(
            r"единолично спроектировал(а)? распределённ",
            body_lower,
        ):
            score -= 8
            issues.append("Middle не должен единолично проектировать всю распределённую систему.")

        profile_tech = {
            tech.lower()
            for role in profile.roles
            for tech in role.technologies
        }
        profile_tech.update(skill.lower() for skill in analysis.required_skills)
        extra = []
        for item in resume.experience:
            for tech in item.technologies:
                if tech.lower() not in profile_tech and tech.lower() not in extra:
                    extra.append(tech.lower())
        if extra:
            score -= min(15, 5 * len(extra))
            issues.append(
                "В резюме есть технологии вне карьерного профиля: "
                + ", ".join(extra[:5])
                + "."
            )
        return score

    def _career(self, profile: CareerProfile, resume: ResumeDocument, issues: list[str]) -> int:
        score = 95
        if profile.issues:
            score -= 8 * len(profile.issues)
            issues.extend(profile.issues)
        companies = [item.company for item in resume.experience if item.company != "NDA"]
        if len(companies) != len(set(companies)):
            score -= 10
            issues.append("Названия компаний в опыте повторяются.")
        if profile.candidate.education and resume.education != list(profile.candidate.education):
            score -= 15
            issues.append("Образование в резюме не совпадает с данными кандидата.")
        if profile.candidate.languages and resume.languages != list(profile.candidate.languages):
            score -= 12
            issues.append("Языки в резюме не совпадают с данными кандидата.")
        if len(resume.experience) != len(profile.roles):
            score -= 10
            issues.append("Число мест работы не совпадает с карьерным профилем.")
        return score

    def _ats(
        self,
        analysis: VacancyAnalysis,
        resume: ResumeDocument,
        body_lower: str,
        issues: list[str],
    ) -> int:
        score = 95
        if not resume.skills:
            score -= 20
            issues.append("Не заполнен блок ключевых навыков — ATS не увидит стек.")
        missing = [
            skill
            for skill in analysis.required_skills[:5]
            if not _contains_skill(body_lower, skill)
        ]
        if missing:
            score -= 6 * len(missing)
        return score
