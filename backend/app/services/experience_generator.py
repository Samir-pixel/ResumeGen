"""Генератор рабочего опыта — создаёт конкретные задачи с причинно-следственной структурой."""
from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.schemas import ExperienceTask, Project, VacancyAnalysis

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path("prompts/experience_generator/system.md")


class _TaskBatch(BaseModel):
    tasks: list[ExperienceTask]


# Большой набор шаблонов задач — используется в эвристическом режиме
_TASK_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "async_offload",
        "problem": (
            "Several HTTP endpoints performed synchronous operations that took 1–3 seconds "
            "per request, degrading user-facing response times during peak load."
        ),
        "task": (
            "Move non-critical processing — email notifications, audit log writes, "
            "and file uploads — out of the request cycle."
        ),
        "actions": [
            "Identified which operations could run asynchronously by analysing response time logs.",
            "Wrapped target operations in Celery tasks with Redis as the broker.",
            "Added task status tracking so the frontend could display progress without blocking.",
            "Tested retry behaviour and failure handling under simulated broker downtime.",
        ],
        "technologies": ["Celery", "Redis", "FastAPI", "Pytest"],
        "reason": (
            "These operations did not need to complete before the HTTP response "
            "and could be retried independently, making Celery the natural fit."
        ),
        "result": (
            "Average endpoint response time dropped from roughly 2.1 s to under 300 ms "
            "for the affected routes."
        ),
        "business_impact": "Users experienced faster feedback, reducing support requests about slow responses.",
        "technical_impact": "Decoupled business-critical path from auxiliary operations; simplified retry logic.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["Celery", "Redis", "RabbitMQ"],
    },
    {
        "id": "reporting_refactor",
        "problem": (
            "Reporting queries contained duplicated filter logic scattered across multiple views, "
            "making it hard to add new report types without risking inconsistency."
        ),
        "task": (
            "Consolidate query construction into a shared layer and add regression tests "
            "for the main reporting cases."
        ),
        "actions": [
            "Audited all existing reporting queries to identify duplicated filter patterns.",
            "Extracted shared filter logic into composable query builder functions.",
            "Wrote parametrised Pytest tests covering edge cases and boundary conditions.",
            "Coordinated with the analytics team to validate output against known reference data.",
        ],
        "technologies": ["PostgreSQL", "SQLAlchemy", "Pytest"],
        "reason": (
            "SQLAlchemy's composable query construction aligned naturally "
            "with the required filter reuse pattern."
        ),
        "result": (
            "Adding a new report type dropped from a multi-day task to a matter of hours; "
            "no regressions were detected in the following two releases."
        ),
        "business_impact": "Reduced time to deliver new reporting requirements by the analytics team.",
        "technical_impact": "Eliminated duplicated filter logic and increased test coverage for the reporting module.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["PostgreSQL", "SQLAlchemy"],
    },
    {
        "id": "integration_error_handling",
        "problem": (
            "External integration failures surfaced to end users as generic 500 errors "
            "with no actionable information, complicating support investigation."
        ),
        "task": (
            "Implement structured error handling, configurable retries, "
            "and a status-tracking table for all third-party integration calls."
        ),
        "actions": [
            "Mapped failure modes for each external service (timeout, auth error, malformed response).",
            "Created a standardised integration wrapper with typed error categories.",
            "Added a `integration_events` table to record call outcomes and retry history.",
            "Updated the admin panel to surface integration status per transaction.",
        ],
        "technologies": ["FastAPI", "PostgreSQL", "Docker"],
        "reason": (
            "PostgreSQL's JSONB column offered a flexible schema for logging varied "
            "integration payloads without requiring separate tables per integration."
        ),
        "result": (
            "Support team could identify and resolve the root cause of failed integrations "
            "in minutes rather than hours; user-visible error messages became actionable."
        ),
        "business_impact": "Shortened resolution time for integration-related support tickets.",
        "technical_impact": "Introduced a reusable integration wrapper adopted by two additional integrations.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["FastAPI", "Django", "DRF"],
    },
    {
        "id": "api_migration",
        "problem": (
            "An internal API endpoint had accumulated breaking changes over time, "
            "and downstream consumers were using different undocumented behaviours."
        ),
        "task": (
            "Version the endpoint, document the contract, "
            "and migrate consumers to the new version with a compatibility shim."
        ),
        "actions": [
            "Documented the current implicit contract by reviewing all consumer call sites.",
            "Introduced versioned routing and moved new logic to /v2 while keeping /v1 intact.",
            "Wrote a compatibility shim mapping v1 responses to v2 schema for existing consumers.",
            "Coordinated with frontend and partner teams on a phased migration timeline.",
        ],
        "technologies": ["FastAPI", "Pydantic", "Pytest"],
        "reason": (
            "Pydantic models made it straightforward to define strict schemas for both versions "
            "and generate accurate OpenAPI documentation automatically."
        ),
        "result": (
            "All consumers migrated to v2 within one sprint; the shim was removed "
            "in the following release with no reported regressions."
        ),
        "business_impact": "Eliminated the risk of silent breaking changes reaching production consumers.",
        "technical_impact": "Established API versioning as a standard practice for the team.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["FastAPI", "Django", "DRF"],
    },
    {
        "id": "db_query_optimisation",
        "problem": (
            "A frequently accessed listing page took 4–6 seconds to load "
            "due to N+1 queries and missing indexes on filtered columns."
        ),
        "task": (
            "Identify the slow queries, fix the ORM access patterns, "
            "and add targeted database indexes."
        ),
        "actions": [
            "Enabled query logging and identified the top 5 slow queries using EXPLAIN ANALYSE.",
            "Replaced N+1 ORM patterns with joined or prefetched queries.",
            "Added composite indexes on the most-filtered column combinations.",
            "Validated that existing integration tests still passed after index changes.",
        ],
        "technologies": ["PostgreSQL", "SQLAlchemy", "Pytest"],
        "reason": (
            "EXPLAIN ANALYSE provided query execution plans that pinpointed sequential scans "
            "on high-cardinality columns, directly guiding index placement."
        ),
        "result": "The listing page load time dropped from 5 s to under 400 ms on production data.",
        "business_impact": "Improved perceived performance for the most-visited page in the application.",
        "technical_impact": "Established a query review checklist used during subsequent code reviews.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["PostgreSQL", "SQLAlchemy"],
    },
    {
        "id": "event_streaming",
        "problem": (
            "Business events generated by one service had to be consumed by three downstream "
            "services, currently connected through direct HTTP calls that created tight coupling."
        ),
        "task": (
            "Decouple producers and consumers by routing domain events through a message bus."
        ),
        "actions": [
            "Designed an event schema for the main domain events, using Pydantic for validation.",
            "Configured Kafka topics with appropriate partition count and retention settings.",
            "Implemented producer-side publishing alongside the existing HTTP calls during rollout.",
            "Migrated two downstream consumers to the Kafka topic and verified offset management.",
        ],
        "technologies": ["Kafka", "Python", "PostgreSQL"],
        "reason": (
            "Kafka's durable log and consumer group model allowed each downstream service "
            "to read at its own pace without affecting producers or other consumers."
        ),
        "result": (
            "Downstream services became independent of producer availability; "
            "two of three consumers were migrated within the quarter."
        ),
        "business_impact": "Reduced cascading failures when one downstream service experienced downtime.",
        "technical_impact": "Established an event-driven integration pattern adopted for two further integrations.",
        "complexity": {"Junior": 3, "Middle": 4, "Senior": 4},
        "requires_any": ["Kafka", "RabbitMQ"],
    },
    {
        "id": "caching_layer",
        "problem": (
            "Reference data endpoints — product lists, configuration values, lookup tables — "
            "were queried on every request, adding unnecessary database load."
        ),
        "task": (
            "Introduce a caching layer for reference data with appropriate TTL "
            "and cache invalidation on data updates."
        ),
        "actions": [
            "Identified reference data endpoints by frequency and data change rate.",
            "Implemented Redis-based caching with configurable TTL per data type.",
            "Added cache-aside invalidation triggered by admin update events.",
            "Monitored cache hit rate and adjusted TTL values based on observed patterns.",
        ],
        "technologies": ["Redis", "FastAPI", "PostgreSQL"],
        "reason": (
            "Redis provided sub-millisecond reads with simple expiry semantics, "
            "matching the read-heavy, occasionally updated nature of reference data."
        ),
        "result": (
            "Database queries for reference endpoints dropped by roughly 80%; "
            "cache hit rate stabilised at 92% after TTL tuning."
        ),
        "business_impact": "Freed database capacity for write-heavy transactional queries.",
        "technical_impact": "Established a reusable caching decorator applied to four additional endpoints.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["Redis"],
    },
    {
        "id": "background_jobs_monitoring",
        "problem": (
            "Background data processing jobs ran silently — failures were only discovered "
            "when downstream data was visibly wrong, sometimes hours later."
        ),
        "task": (
            "Add monitoring, alerting, and structured logging for background job execution."
        ),
        "actions": [
            "Added structured log entries at job start, completion, and failure with job metadata.",
            "Stored job execution records in a `job_runs` table with status, duration, and error.",
            "Implemented an admin endpoint to review recent job history and re-trigger failed jobs.",
            "Set up a simple health-check endpoint consumed by the deployment pipeline.",
        ],
        "technologies": ["Celery", "Redis", "PostgreSQL", "FastAPI"],
        "reason": (
            "Storing execution history in PostgreSQL allowed querying across job runs "
            "without relying on Redis TTL-limited task metadata."
        ),
        "result": (
            "Average time to detect and respond to job failures dropped from several hours "
            "to under 10 minutes once the admin panel showed live job status."
        ),
        "business_impact": "Operations team could proactively resolve data inconsistencies before users noticed.",
        "technical_impact": "Provided full execution history for debugging and capacity planning.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["Celery"],
    },
    {
        "id": "schema_migration",
        "problem": (
            "A growing table required a new column and an associated index, "
            "but the migration had to run on a live database with zero downtime."
        ),
        "task": (
            "Design and execute a backwards-compatible zero-downtime migration "
            "for the high-traffic table."
        ),
        "actions": [
            "Added the column as nullable in a first migration to avoid locking the table.",
            "Backfilled existing rows in batches during off-peak hours to avoid locking.",
            "Applied the NOT NULL constraint and index concurrently once backfill was complete.",
            "Validated row counts and sample data before and after each migration step.",
        ],
        "technologies": ["PostgreSQL", "Alembic", "Python"],
        "reason": (
            "Alembic's sequential migration model and PostgreSQL's concurrent index creation "
            "allowed splitting the operation across three safe steps."
        ),
        "result": (
            "Migration ran on the production table with no downtime or query slowdowns "
            "observed by the monitoring system."
        ),
        "business_impact": "Enabled a new product feature dependent on the column without a maintenance window.",
        "technical_impact": "Established a zero-downtime migration pattern documented in the team runbook.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["Alembic", "PostgreSQL"],
    },
    {
        "id": "auth_module",
        "problem": (
            "The application used a basic session approach that did not support "
            "multi-device access or programmatic API clients."
        ),
        "task": (
            "Replace session-based auth with JWT-based authentication "
            "while keeping existing sessions valid during the transition."
        ),
        "actions": [
            "Designed the token schema: short-lived access tokens and rotating refresh tokens.",
            "Implemented token issuance, validation, and revocation endpoints.",
            "Added a middleware layer that accepted both session cookies and Bearer tokens.",
            "Coordinated frontend migration to the new auth header in parallel.",
        ],
        "technologies": ["FastAPI", "PostgreSQL", "Redis"],
        "reason": (
            "JWT allowed stateless verification for most requests, "
            "while Redis-stored revocation lists handled logout and token invalidation."
        ),
        "result": (
            "Mobile and API consumers could authenticate without session cookies; "
            "no breaking changes reported during the migration period."
        ),
        "business_impact": "Enabled third-party integrations that required token-based API access.",
        "technical_impact": "Standardised authentication across REST and future WebSocket endpoints.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["FastAPI", "Django"],
    },
    {
        "id": "test_coverage",
        "problem": (
            "Core business logic had minimal test coverage, leading to frequent regressions "
            "in the payment and order processing paths after each release."
        ),
        "task": (
            "Establish a meaningful test suite for the critical business logic "
            "and integrate it into the CI pipeline."
        ),
        "actions": [
            "Mapped the riskiest code paths by reviewing bug reports from the last six months.",
            "Wrote unit tests using pytest fixtures and factory_boy for model generation.",
            "Added integration tests against a real PostgreSQL instance using pytest-asyncio.",
            "Configured GitHub Actions to block merges when coverage dropped below 80%.",
        ],
        "technologies": ["Pytest", "PostgreSQL", "Docker"],
        "reason": (
            "Pytest's parametrize and fixture system made it easy to cover edge cases "
            "without duplicating setup code across test files."
        ),
        "result": (
            "Test coverage on the core payment module rose from 12% to 84% in two sprints; "
            "the following three releases contained no regressions in that area."
        ),
        "business_impact": "Reduced the number of production hotfixes related to payment processing by 70%.",
        "technical_impact": "Established a test pyramid pattern adopted by the full backend team.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["Pytest", "FastAPI", "Django"],
    },
    {
        "id": "rate_limiting",
        "problem": (
            "Public API endpoints were vulnerable to abuse, with some clients sending "
            "hundreds of requests per second and degrading service quality for others."
        ),
        "task": (
            "Implement per-client rate limiting using a sliding window algorithm "
            "with configurable limits per endpoint tier."
        ),
        "actions": [
            "Evaluated token bucket vs sliding window strategies for the traffic pattern.",
            "Implemented a Redis-backed sliding window counter keyed by client API key.",
            "Added rate-limit headers (X-RateLimit-Limit, Remaining, Reset) to all responses.",
            "Tested behaviour under burst traffic using a load simulation script.",
        ],
        "technologies": ["Redis", "FastAPI", "Python"],
        "reason": (
            "Redis atomic INCR with EXPIRE allowed a correct sliding window implementation "
            "without requiring a dedicated rate-limit service."
        ),
        "result": (
            "Abusive clients were automatically throttled within seconds of threshold breach; "
            "average response latency for legitimate users dropped by 35%."
        ),
        "business_impact": "Prevented SLA violations caused by uncontrolled bursts from misbehaving API consumers.",
        "technical_impact": "Rate limiting middleware reused across four separate API gateway endpoints.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["Redis", "FastAPI"],
    },
    {
        "id": "data_pipeline",
        "problem": (
            "Analytical reports relied on real-time database queries that locked rows "
            "and visibly slowed down the transactional API during business hours."
        ),
        "task": (
            "Build a nightly ETL pipeline that materialises aggregate report data "
            "into a dedicated reporting schema."
        ),
        "actions": [
            "Designed the reporting schema with pre-aggregated tables optimised for read access.",
            "Implemented incremental extraction to process only records changed since last run.",
            "Scheduled the pipeline using Celery beat with monitoring via job_runs table.",
            "Added reconciliation checks comparing pipeline output to spot-check queries.",
        ],
        "technologies": ["PostgreSQL", "Celery", "SQLAlchemy"],
        "reason": (
            "Separating the analytical read model from the transactional schema eliminated "
            "the row-lock contention that was causing API latency spikes."
        ),
        "result": (
            "Report generation moved from 15–30 s real-time queries to sub-second reads "
            "from the reporting schema; transactional API latency normalised during peak hours."
        ),
        "business_impact": "Analytics team could run ad-hoc queries without impacting live users.",
        "technical_impact": "Established a CQRS-lite pattern applied to two additional reporting modules.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["PostgreSQL", "Celery", "SQLAlchemy"],
    },
    {
        "id": "rbac",
        "problem": (
            "Permission checks were hardcoded throughout the codebase, making it difficult "
            "to add new roles without touching dozens of endpoint handlers."
        ),
        "task": (
            "Design and implement a role-based access control system "
            "decoupled from endpoint business logic."
        ),
        "actions": [
            "Mapped existing implicit permission requirements across all 40+ endpoints.",
            "Designed a permissions table with role → resource → action granularity.",
            "Implemented a dependency-injection-based permission checker for FastAPI.",
            "Wrote permission matrix tests covering all role/resource combinations.",
        ],
        "technologies": ["FastAPI", "PostgreSQL", "Pytest"],
        "reason": (
            "FastAPI's dependency injection system allowed attaching permission checks "
            "declaratively at the route level without duplicating logic in handler bodies."
        ),
        "result": (
            "Adding a new role dropped from a multi-day cross-cutting change to a "
            "single database record and a permission matrix update."
        ),
        "business_impact": "Enabled onboarding of a new enterprise client tier requiring custom permission sets.",
        "technical_impact": "Centralised all permission logic, reducing endpoint code by an average of 15 lines each.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["FastAPI", "Django", "PostgreSQL"],
    },
    {
        "id": "feature_flags",
        "problem": (
            "Releasing new features required full deployments, making it impossible to "
            "test changes with a subset of users or roll back quickly without redeploying."
        ),
        "task": (
            "Introduce a lightweight feature flag system to enable gradual rollouts "
            "and per-tenant feature control."
        ),
        "actions": [
            "Defined a feature_flags table with tenant-level overrides and default values.",
            "Implemented a cached flag resolver backed by Redis for low-latency lookups.",
            "Added a flag evaluation decorator usable on individual API endpoints.",
            "Created an admin interface to toggle flags without a deployment.",
        ],
        "technologies": ["Redis", "PostgreSQL", "FastAPI"],
        "reason": (
            "Caching flag states in Redis with a short TTL kept evaluation latency "
            "under 1 ms while allowing near-instant propagation of flag changes."
        ),
        "result": (
            "The team shipped three consecutive features to 5% of users first, "
            "catching two UX issues before full rollout."
        ),
        "business_impact": "Reduced risk of large-scale rollouts and enabled A/B testing without code changes.",
        "technical_impact": "Flag system adopted for 12 features in the following quarter.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["Redis", "FastAPI", "Django"],
    },
    {
        "id": "observability",
        "problem": (
            "When production incidents occurred, the team had no structured way to trace "
            "a failed request across service boundaries, making root-cause analysis slow."
        ),
        "task": (
            "Add structured logging, request tracing, and performance metrics "
            "to the main service."
        ),
        "actions": [
            "Replaced print-style logging with structured JSON logs using a shared logger config.",
            "Added a request-ID middleware propagating a trace ID through all downstream calls.",
            "Instrumented the five slowest endpoints with timing metrics exported to Prometheus.",
            "Created a Grafana dashboard showing p50/p95/p99 latencies and error rates.",
        ],
        "technologies": ["FastAPI", "Python", "PostgreSQL"],
        "reason": (
            "Structured logs made it possible to filter by trace ID across log aggregation tools "
            "without needing a dedicated distributed tracing infrastructure."
        ),
        "result": (
            "Mean time to diagnose a production incident dropped from 45 minutes to under 10 minutes "
            "in the first month after deployment."
        ),
        "business_impact": "On-call engineers could resolve incidents faster, reducing user-facing downtime.",
        "technical_impact": "Logging and tracing patterns adopted as team standard for all new services.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 4},
        "requires_any": ["FastAPI", "Django", "Python"],
    },
    {
        "id": "pagination_bulk",
        "problem": (
            "Admin export endpoints returned all records in a single response, "
            "causing timeouts for datasets larger than 10 000 rows."
        ),
        "task": (
            "Replace offset-based pagination with keyset pagination and add "
            "a streaming CSV export endpoint for large datasets."
        ),
        "actions": [
            "Replaced OFFSET queries with keyset pagination on the primary sort key.",
            "Implemented a streaming response endpoint using FastAPI's StreamingResponse.",
            "Added server-side row limits and a cursor token scheme for safe deep pagination.",
            "Benchmarked both approaches on a 500K-row test dataset to confirm improvement.",
        ],
        "technologies": ["FastAPI", "PostgreSQL", "SQLAlchemy"],
        "reason": (
            "Keyset pagination avoids the performance cliff of large OFFSET values "
            "and enables stable cursors regardless of concurrent inserts."
        ),
        "result": (
            "Admin export of 100K records went from a 30-second timeout to a streaming "
            "response completing in under 4 seconds."
        ),
        "business_impact": (
            "Operations team could export full transaction histories without "
            "requesting database access."
        ),
        "technical_impact": "Keyset pagination pattern applied to three other high-volume list endpoints.",
        "complexity": {"Junior": 2, "Middle": 3, "Senior": 3},
        "requires_any": ["FastAPI", "PostgreSQL", "SQLAlchemy"],
    },
]


class ExperienceGenerator:
    def __init__(self, llm=None) -> None:
        self.llm = llm
        self._prompt: str | None = None
        # Отслеживаем использованные шаблоны для разнообразия
        self.last_selected_ids: set[str] = set()

    async def create_tasks(
        self,
        project: Project,
        analysis: VacancyAnalysis,
        rng: random.Random,
        excluded_ids: set[str] | None = None,
    ) -> list[ExperienceTask]:
        if self.llm:
            return await self._create_with_llm(project, analysis)
        return self._create_heuristic(project, analysis, rng, excluded_ids or set())

    # ── LLM path ───────────────────────────────────────────────────────────────

    async def _create_with_llm(self, project: Project, analysis: VacancyAnalysis) -> list[ExperienceTask]:
        system = self._load_prompt()
        task_count = 2 if analysis.seniority == "Junior" else 3
        context = (
            f"Проект: {project.name}\n"
            f"Описание: {project.description}\n"
            f"Архитектура: {project.architecture}\n"
            f"Технологии: {', '.join(project.technologies)}\n"
            f"Интеграции: {', '.join(project.integrations)}\n"
            f"Роль кандидата: backend-разработчик уровня {analysis.seniority}\n"
            f"Домен: {analysis.domain}\n"
            f"Обязательные навыки: {', '.join(analysis.required_skills)}\n\n"
            f"Создай ровно {task_count} реалистичные задачи. "
            "Вся человеческая проза должна быть на русском языке."
        )
        logger.info("ExperienceGenerator: LLM call (%s)", project.name)
        batch = await self.llm.generate(system, context, _TaskBatch)
        return batch.tasks[:task_count]

    def _load_prompt(self) -> str:
        if self._prompt is None:
            try:
                self._prompt = _PROMPT_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._prompt = (
                    "Создавай реалистичные задачи для резюме разработчика по структуре STAR. "
                    "Вся человеческая проза должна быть на русском языке. "
                    "Верни JSON с массивом tasks."
                )
        return self._prompt

    # ── Heuristic path ─────────────────────────────────────────────────────────

    def _create_heuristic(
        self,
        project: Project,
        analysis: VacancyAnalysis,
        rng: random.Random,
        excluded_ids: set[str] | None = None,
    ) -> list[ExperienceTask]:
        excluded_ids = excluded_ids or set()
        # Фильтруем по технологиям проекта, исключая уже использованные шаблоны
        relevant = [
            t for t in _TASK_TEMPLATES
            if any(tech in project.technologies for tech in t.get("requires_any", []))
            and t["id"] not in excluded_ids
        ]
        # Если после исключения шаблонов слишком мало — используем все нейспользованные
        if len(relevant) < 2:
            relevant = [t for t in _TASK_TEMPLATES if t["id"] not in excluded_ids]
        # Последний fallback — все шаблоны
        if len(relevant) < 2:
            relevant = _TASK_TEMPLATES

        task_count = 2 if analysis.seniority == "Junior" else 3
        selected = rng.sample(relevant, k=min(task_count, len(relevant)))

        # Запоминаем использованные ID
        self.last_selected_ids = {t["id"] for t in selected}

        return [self._make_task(project, item, analysis.seniority) for item in selected]

    def _make_task(
        self, project: Project, template: dict, seniority: str
    ) -> ExperienceTask:
        # Фильтруем технологии шаблона по тому, что есть в проекте
        used_techs = [
            t for t in template["technologies"]
            if t in project.technologies
        ] or template["technologies"][:2]

        complexity_map: dict = template.get("complexity", {"Junior": 2, "Middle": 3, "Senior": 4})
        complexity = complexity_map.get(seniority, 3)

        return ExperienceTask(
            context=f"While working on {project.name} — {project.description[:80]}.",
            problem=template["problem"],
            task=template["task"],
            actions=template["actions"],
            technologies=used_techs,
            reason=template["reason"],
            constraints=[
                "Existing API contracts had to remain stable.",
                "Changes needed to fit within the current sprint scope.",
            ],
            result=template["result"],
            complexity=complexity,
            business_impact=template["business_impact"],
            technical_impact=template["technical_impact"],
        )
