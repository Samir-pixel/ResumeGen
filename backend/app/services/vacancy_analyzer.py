"""Анализатор вакансии — извлекает структурированные данные из произвольного текста."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from app.schemas import VacancyAnalysis
from app.services.knowledge_base import DEFAULT_DOMAIN, DOMAIN_PATTERNS, TECH_CATALOG
from app.services.knowledge_base_ru import NDA_DOMAINS, NDA_KEYWORDS, RU_DOMAIN_KEYWORDS

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path("prompts/vacancy_analyzer/system.md")


class VacancyAnalyzer:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None

    async def analyze(self, raw_vacancy: str) -> VacancyAnalysis:
        if self.llm:
            return await self._analyze_with_llm(raw_vacancy)
        return self._analyze_heuristic(raw_vacancy)

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _analyze_with_llm(self, raw_vacancy: str) -> VacancyAnalysis:
        system = self._load_prompt()
        user = f"Проанализируй вакансию. Ответ и вся описательная информация — на русском:\n\n{raw_vacancy}"
        logger.info("VacancyAnalyzer: LLM call")
        analysis = await self.llm.generate(system, user, VacancyAnalysis)
        # Seniority is deterministic business data. Smaller models sometimes
        # return Senior for vacancies explicitly asking for 3–4 years.
        lowered = raw_vacancy.lower()
        analysis.seniority = self._extract_seniority(lowered)
        analysis.language = self._extract_language(raw_vacancy)
        # Домен от модели бывает произвольным ("Marketing Data"), а от него
        # зависит выбор пула компаний — берём эвристический.
        analysis.domain = self._extract_domain(lowered)
        analysis.is_nda_domain = self._extract_nda(lowered, analysis.domain, analysis.language)
        return analysis

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _PROMPT_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = (
                    "Ты старший HR-аналитик. Проанализируй вакансию и верни JSON "
                    "с должностью, уровнем, навыками, доменом и обязанностями. "
                    "Вся описательная информация должна быть на русском языке."
                )
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _analyze_heuristic(self, raw_vacancy: str) -> VacancyAnalysis:
        text = raw_vacancy.strip()
        lowered = text.lower()
        skills = self._extract_skills(text)
        seniority = self._extract_seniority(lowered)
        language = self._extract_language(text)
        domain = self._extract_domain(lowered)
        is_nda = self._extract_nda(lowered, domain, language)
        title = self._extract_title(text, seniority, skills)
        responsibilities = self._extract_responsibilities(text)
        required_experience = self._extract_years(lowered, seniority)
        # priority = топ скилы + короткие конкретные обязанности (не длиннее 60 символов)
        short_resp = [r for r in responsibilities if len(r) <= 60 and not any(
            w in r.lower() for w in ["years", "experience", "required"]
        )]
        priority = skills[:5] + short_resp[:2]

        return VacancyAnalysis(
            title=title,
            seniority=seniority,
            required_experience=required_experience,
            required_skills=skills[:10],
            preferred_skills=skills[10:15],
            responsibilities=responsibilities,
            domain=domain,
            language=language,
            is_nda_domain=is_nda,
            company_context=f"Продуктовая компания в сфере {domain}",
            priority_requirements=priority[:7],
        )

    def _extract_language(self, text: str) -> str:
        letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text)
        cyrillic = re.findall(r"[А-Яа-яЁё]", text)
        if letters and len(cyrillic) / len(letters) > 0.3:
            return "ru"
        return "en"

    def _extract_nda(self, lowered: str, domain: str, language: str) -> bool:
        """Скрывать ли работодателей за «NDA».

        Прямое упоминание NDA работает всегда; закрытые сферы (финтех, крипта,
        iGaming) скрываются только для русскоязычных вакансий — так просил
        заказчик, для международного рынка названия компаний остаются.
        """
        if any(keyword in lowered for keyword in NDA_KEYWORDS):
            return True
        return language == "ru" and domain in NDA_DOMAINS

    def _extract_skills(self, text: str) -> list[str]:
        found: list[str] = []
        lowered = text.lower()
        aliases = {
            "aws": "AWS S3",
            "s3": "AWS S3",
            "django rest framework": "DRF",
            "docker compose": "Docker Compose",
            "rabbit": "RabbitMQ",
            "elastic": "Elasticsearch",
            "k8s": "Kubernetes",
        }
        for skill in TECH_CATALOG:
            if skill.lower() in lowered and skill not in found:
                found.append(skill)
        for alias, normalized in aliases.items():
            if alias in lowered and normalized not in found:
                found.append(normalized)
        if "Python" not in found:
            found.insert(0, "Python")
        if "PostgreSQL" not in found:
            found.append("PostgreSQL")
        return found

    def _extract_seniority(self, lowered: str) -> str:
        if re.search(
            r"\bsenior\b|lead developer|tech lead|7\+ years|"
            r"\bведущ(ий|ая)\b|\bстарш(ий|ая)\b|\bтимлид\b|7\+?\s*лет",
            lowered,
        ):
            return "Senior"
        if re.search(
            r"\bjunior\b|trainee|intern|1\+ years?|"
            r"\bмладш(ий|ая)\b|\bстаж[её]р\b|1\+?\s*(?:год|лет)",
            lowered,
        ):
            return "Junior"
        return "Middle"

    def _extract_domain(self, lowered: str) -> str:
        for domain, keywords in RU_DOMAIN_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return domain
        for domain, data in DOMAIN_PATTERNS.items():
            if any(keyword in lowered for keyword in data["keywords"]):
                return domain
        return DEFAULT_DOMAIN

    def _extract_title(self, text: str, seniority: str, skills: list[str]) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        title_markers = [
            "developer", "engineer", "backend", "python", "software",
            "разработчик", "инженер", "бэкенд", "бекенд", "программист",
        ]
        if (
            4 <= len(first_line) <= 80
            and any(tok in first_line.lower() for tok in title_markers)
            and re.search(r"[А-Яа-яЁё]", first_line)
        ):
            return first_line
        seniority_ru = {"Junior": "Младший", "Middle": "", "Senior": "Старший"}
        core = "Python backend-разработчик" if "Python" in skills else "Backend-разработчик"
        return f"{seniority_ru[seniority]} {core}".strip()

    # Признаки что строка — описание должности/требования, а не ответственность
    _NOT_RESPONSIBILITY_PATTERNS = [
        r"\d\+?\s*years?",          # "3+ years"
        r"years?\s+of\s+experience",
        r"experience\s+required",
        r"we\s+(are|offer|provide)",
        r"(salary|compensation|benefits|perks)",
        r"about\s+(us|the\s+(company|team))",
        r"(send|submit|apply)\s+(your|cv|resume)",
        r"\d+\s*(?:лет|года|год)\s+опыта",
        r"(мы\s+(предлагаем|ищем)|условия|зарплата|о\s+компании)",
    ]

    def _extract_responsibilities(self, text: str) -> list[str]:
        import re as _re
        candidates = []
        not_resp_re = [_re.compile(p, _re.IGNORECASE) for p in self._NOT_RESPONSIBILITY_PATTERNS]

        for line in text.splitlines():
            normalized = line.strip(" -\t*•")
            # Фильтры длины
            if not (20 <= len(normalized) <= 120):
                continue
            # Не выглядит как требование/описание компании
            if any(r.search(normalized) for r in not_resp_re):
                continue
            # Должна содержать глагол действия (что делает разработчик)
            action_words = [
                "develop", "design", "support", "integrat", "test",
                "review", "maintain", "build", "implement", "write",
                "creat", "deploy", "monitor", "optimis", "refactor",
                "participat", "collaborat", "analyz",
                "разрабаты", "проектир", "поддерж", "интегр", "тестир",
                "реализ", "созда", "внедр", "оптимиз", "участв",
                "анализир", "сопровожд", "улучша",
            ]
            if any(w in normalized.lower() for w in action_words):
                candidates.append(normalized)

        fallback = [
            "Разработка backend API и бизнес-логики продукта",
            "Интеграция внутренних и внешних сервисов",
            "Повышение надёжности, качества тестов и запросов к базе данных",
        ]
        return (candidates + fallback)[:8]

    def _extract_years(self, lowered: str, seniority: str) -> int:
        matches = re.findall(r"(\d+)\s*\+?\s*(?:years?|лет|года|год)", lowered)
        if matches:
            return min(max(int(matches[0]), 0), 20)
        return {"Junior": 1, "Middle": 3, "Senior": 6}[seniority]
