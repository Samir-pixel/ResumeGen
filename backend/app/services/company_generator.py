"""Генератор компаний — создаёт реалистичные профили работодателей."""
from __future__ import annotations

import logging
import random
from pathlib import Path

from pydantic import BaseModel

from app.schemas import Company
from app.services.knowledge_base import (
    COMPANY_LOCATIONS,
    DEFAULT_DOMAIN,
    DOMAIN_PATTERNS,
    OUTSOURCE_COMPANIES,
    OUTSOURCE_PROBABILITY,
)
from app.services.knowledge_base_ru import (
    NDA_COMPANY_NAME,
    NDA_LOCATION,
    NDA_SECTOR_LABELS,
    RU_LOCATIONS,
    RU_OUTSOURCE_COMPANIES,
    ru_domain_data,
)

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path("prompts/company_generator/system.md")


class _CompanyBatch(BaseModel):
    """Вспомогательная схема для LLM: список компаний одним вызовом."""
    companies: list[Company]


class CompanyGenerator:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None

    async def create(
        self,
        domain: str,
        index: int,
        rng: random.Random,
        used_names: set[str] | None = None,
        language: str = "en",
        is_nda: bool = False,
    ) -> Company:
        # NDA-работодателя незачем спрашивать у модели: название фиксировано,
        # а остальные поля должны остаться обезличенными.
        if self.llm and not is_nda:
            return await self._create_with_llm(domain, index, used_names or set(), language)
        return self._create_heuristic(domain, index, rng, language, is_nda)

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _create_with_llm(
        self, domain: str, index: int, used_names: set[str], language: str
    ) -> Company:
        system = self._load_prompt()

        if language == "ru":
            data = ru_domain_data(domain)
            approved_names = data["companies"]
            outsource_names = [company["name"] for company in RU_OUTSOURCE_COMPANIES]
            region_clause = (
                "Вакансия на русском языке, поэтому работодатели должны быть "
                "компаниями из России, Казахстана или Беларуси."
            )
        else:
            domain_data = DOMAIN_PATTERNS.get(domain, DOMAIN_PATTERNS[DEFAULT_DOMAIN])
            approved_names = domain_data.get("company_names", [])
            outsource_names = [company["name"] for company in OUTSOURCE_COMPANIES]
            region_clause = "Работодатели — международные компании."

        exclude_clause = (
            f"\nНе используй уже выбранные компании: {', '.join(sorted(used_names))}"
            if used_names else ""
        )
        position = (
            "текущий работодатель" if index == 0 else f"предыдущий работодатель №{index}"
        )

        context = (
            f"Домен: {domain}\n"
            f"Позиция в карьере: {position}\n"
            f"{region_clause}"
            f"{exclude_clause}\n\n"
            "ВАЖНО: выбери название ТОЛЬКО из списка ниже. Не придумывай компании.\n"
            "Всю описательную информацию верни на русском языке.\n\n"
            f"Разрешённые продуктовые компании для {domain}:\n"
            + "\n".join(f"  - {name}" for name in approved_names[:10])
            + "\n\nРазрешённые аутсорсинговые компании:\n"
            + "\n".join(f"  - {name}" for name in outsource_names[:6])
            + "\n\nВыбери подходящую компанию и заполни реалистичные сведения по-русски."
        )
        logger.info("CompanyGenerator: LLM call (domain=%s, index=%d)", domain, index)
        return await self.llm.generate(system, context, Company)

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _PROMPT_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = (
                    "Создай реалистичный профиль компании для резюме. "
                    "Всю описательную информацию верни на русском языке. "
                    "Название выбери только из переданного разрешённого списка."
                )
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _create_heuristic(
        self,
        domain: str,
        index: int,
        rng: random.Random,
        language: str = "en",
        is_nda: bool = False,
    ) -> Company:
        if is_nda:
            return self._create_nda_company(domain, index, rng)
        # ~30% шанс использовать аутсорс/аутстафф компанию (для не-первой позиции — выше)
        use_outsource_chance = OUTSOURCE_PROBABILITY if index == 0 else OUTSOURCE_PROBABILITY + 0.15
        if rng.random() < use_outsource_chance:
            return self._create_outsource(domain, rng, language)
        return self._create_product_company(domain, index, rng, language)

    def _create_nda_company(self, domain: str, index: int, rng: random.Random) -> Company:
        """Работодатель под NDA: сфера и масштаб раскрыты, название — нет."""
        data = ru_domain_data(domain)
        sector = NDA_SECTOR_LABELS.get(domain, f"{domain} (NDA)")
        product = rng.choice(data["products"])
        return Company(
            name=NDA_COMPANY_NAME,
            industry=domain,
            sector=sector,
            employees=rng.randint(80, 900),
            location=NDA_LOCATION,
            business_description=(
                f"Компания не раскрывается по условиям NDA. Продукт — {product}; "
                f"пользователи — {data['users']}."
            ),
        )

    def _create_outsource(self, domain: str, rng: random.Random, language: str) -> Company:
        """Создаёт аутсорс/аутстафф компанию с упоминанием домена клиента."""
        if language == "ru":
            company_data = rng.choice(RU_OUTSOURCE_COMPANIES)
            sector_label = ru_domain_data(domain)["sectors"][0]
            client_clause = (
                f"Кандидат вёл проект клиента из сферы «{sector_label}» "
                "в составе выделенной команды."
            )
        else:
            company_data = rng.choice(OUTSOURCE_COMPANIES)
            client_clause = (
                f"The candidate worked on a {domain.lower()} client project "
                "as part of a dedicated team."
            )

        low, high = company_data["employees_range"]
        return Company(
            name=company_data["name"],
            industry=f"IT Services ({domain} client)",
            sector=company_data["sector"],
            employees=rng.randint(low, high),
            location=rng.choice(company_data["locations"]),
            business_description=f"{company_data['description']} {client_clause}",
        )

    def _create_product_company(
        self, domain: str, index: int, rng: random.Random, language: str
    ) -> Company:
        """Создаёт продуктовую компанию из заданного домена."""
        if language == "ru":
            data = ru_domain_data(domain)
            names = data["companies"]
            sectors = data["sectors"]
            locations = RU_LOCATIONS
        else:
            domain_data = DOMAIN_PATTERNS.get(domain, DOMAIN_PATTERNS[DEFAULT_DOMAIN])
            names = domain_data.get("company_names", [])
            sectors = domain_data.get("sectors", ["Technology"])
            locations = COMPANY_LOCATIONS

        name = rng.choice(names) if names else f"{domain}Corp"
        sector = rng.choice(sectors)

        size_options = [
            (30, 120),
            (120, 500),
            (500, 2000),
        ]
        if index == 0:
            low, high = rng.choice(size_options[:2])  # актуальная работа — среднего размера
        else:
            low, high = rng.choice(size_options)

        if language == "ru":
            data = ru_domain_data(domain)
            description = (
                f"{name} развивает продукт в сфере «{sector}»: "
                f"{rng.choice(data['products'])}. "
                f"Основные пользователи — {data['users']}."
            )
        else:
            domain_data = DOMAIN_PATTERNS.get(domain, DOMAIN_PATTERNS[DEFAULT_DOMAIN])
            description = (
                f"A {sector.lower()} company building a {rng.choice(domain_data['products'])}. "
                f"Serves {_target_for(domain)} across multiple regions."
            )

        return Company(
            name=name,
            industry=domain,
            sector=sector,
            employees=rng.randint(low, high),
            location=rng.choice(locations),
            business_description=description,
        )


def _target_for(domain: str) -> str:
    targets = {
        "FinTech": "financial institutions and SMEs",
        "E-commerce": "online retailers and marketplaces",
        "SaaS": "B2B software customers",
        "Logistics": "logistics operators and carriers",
        "Healthcare": "clinics, hospitals, and patients",
        "ERP": "mid-size and enterprise companies",
        "EdTech": "learners and corporate clients",
        "iGaming": "gaming operators and players",
        "Telecom": "mobile operators and subscribers",
    }
    return targets.get(domain, "business customers")
