from app.schemas import (
    Candidate,
    CareerProfile,
    Company,
    ExperienceTask,
    Project,
    QualityScores,
    ResumeDocument,
    ResumeExperience,
    RoleExperience,
    Team,
    VacancyAnalysis,
)
from app.services.quality_scorer import PASS_THRESHOLD, ResumeQualityScorer


def _analysis() -> VacancyAnalysis:
    return VacancyAnalysis(
        title="Python backend-разработчик",
        seniority="Middle",
        required_experience=3,
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        preferred_skills=["Kafka"],
        responsibilities=["Разрабатывать API"],
        domain="SaaS",
        company_context="SaaS",
        priority_requirements=["Python", "FastAPI"],
    )


def _company() -> Company:
    return Company(
        name="Контур",
        industry="SaaS",
        sector="Облачные B2B-сервисы",
        employees=200,
        location="Москва, Россия",
        business_description="Развивает B2B-сервисы.",
    )


def _profile() -> CareerProfile:
    role = RoleExperience(
        company=_company(),
        start_date="2022-01",
        end_date="Present",
        role="Python backend-разработчик",
        project=Project(
            name="Платформа",
            description="Сервис",
            business_purpose="Автоматизация",
            target_users="клиенты",
            scale="10k",
            modules=["API"],
            architecture="сервисы",
            integrations=["CRM"],
            databases=["PostgreSQL"],
            infrastructure=["Docker"],
            technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        ),
        team=Team(
            size=6,
            roles=["Tech Lead", "backend"],
            structure="продуктовая команда",
            candidate_role="backend",
            collaboration="code review",
        ),
        tasks=[
            ExperienceTask(
                context="API",
                problem="медленные запросы",
                task="оптимизация",
                actions=["профиль"],
                technologies=["PostgreSQL"],
                reason="нагрузка",
                constraints=[],
                result="ускорили ответы",
                complexity=3,
                business_impact="стабильность",
                technical_impact="индексы",
            )
        ],
        technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        quality=QualityScores(
            technical_realism=90,
            business_realism=90,
            career_consistency=90,
            seniority_consistency=90,
            language_quality=90,
        ),
    )
    return CareerProfile(
        candidate=Candidate(
            name="Иван Петров",
            age=28,
            city="Казань",
            title="Python backend-разработчик",
            seniority="Middle",
            total_experience_years=4,
            education=["Бакалавр — КФУ, 2017–2021"],
            languages=["Русский — Родной"],
            email="",
            phone="",
        ),
        roles=[role],
        quality_score=90,
    )


def _resume(*, bullets: list[str] | None = None, summary: str | None = None) -> ResumeDocument:
    return ResumeDocument(
        header={"name": "Иван Петров", "city": "Казань"},
        target_position="Python backend-разработчик",
        summary=summary
        or (
            "Middle backend-разработчик с опытом 4 лет в B2B SaaS. "
            "Проектирует API на Python и FastAPI, работает с PostgreSQL, Redis и Docker. "
            "Уделяет внимание тестам, наблюдаемости и сопровождаемости сервисов."
        ),
        skills={
            "Backend-разработка": ["Python", "FastAPI"],
            "Данные и хранение": ["PostgreSQL", "Redis"],
            "Инфраструктура": ["Docker"],
        },
        experience=[
            ResumeExperience(
                company="Контур",
                sector="Облачные B2B-сервисы",
                location="Москва, Россия",
                dates="2022 — н. в.",
                role="Python backend-разработчик",
                company_description="Компания развивает облачные B2B-сервисы.",
                project_description="Платформа автоматизации клиентских процессов на FastAPI.",
                team="Кросс-функциональная команда из 6 специалистов.",
                bullets=bullets
                or [
                    "Спроектировал REST API на FastAPI и покрыл критичные сценарии тестами.",
                    "Оптимизировал запросы PostgreSQL и сократил время ответа отчётов.",
                    "Настроил фоновые задачи и кэш в Redis для пиковой нагрузки.",
                    "Собрал Docker-образы сервисов и упростил локальный запуск команды.",
                ],
                technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
            )
        ],
        education=["Бакалавр — КФУ, 2017–2021"],
        languages=["Русский — Родной"],
    )


def test_strong_resume_passes_threshold() -> None:
    report = ResumeQualityScorer().score(_analysis(), _profile(), _resume())

    assert report.overall_score >= PASS_THRESHOLD
    assert report.relevance >= 80
    assert not any(issue.startswith("[блок]") for issue in report.issues)


def test_missing_skills_and_cliches_fail() -> None:
    resume = _resume(
        summary="Высокомотивированный командный игрок. Нацеленный на результат.",
        bullets=["Участвовал в разработке различных задач."],
    )
    report = ResumeQualityScorer().score(_analysis(), _profile(), resume)

    assert report.overall_score < PASS_THRESHOLD
    assert any("клише" in issue.lower() or "обязательн" in issue.lower() for issue in report.issues)


def test_english_prose_is_hard_fail() -> None:
    resume = _resume(
        summary="Experienced backend engineer building scalable APIs and data pipelines.",
        bullets=[
            "Designed REST APIs and improved database performance.",
            "Implemented background jobs and caching.",
            "Worked on dockerized deployments.",
        ],
    )
    report = ResumeQualityScorer().score(_analysis(), _profile(), resume)

    assert report.overall_score < PASS_THRESHOLD
    assert any("[блок]" in issue for issue in report.issues)
