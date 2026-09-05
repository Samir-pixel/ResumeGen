"""API тесты — health endpoint и полный генерационный flow."""
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_generation_returns_202() -> None:
    """POST /api/v1/generations возвращает 202 с generation_id."""
    payload = {
        "vacancy_text": (
            "Middle Python Backend Developer. "
            "Build FastAPI APIs with PostgreSQL, Redis, Docker, SQLAlchemy and Pytest "
            "for a SaaS platform. 3+ years experience."
        )
    }
    response = client.post("/api/v1/generations", json=payload)
    assert response.status_code == 202, response.text
    body = response.json()
    assert "generation_id" in body
    assert body["status"] == "queued"


def test_get_generation_not_found() -> None:
    response = client.get("/api/v1/generations/nonexistent-id")
    assert response.status_code == 404


def test_create_generation_rejects_invalid_education_years() -> None:
    response = client.post(
        "/api/v1/generations",
        json={
            "vacancy_text": "Python backend-разработчик. Требуется опыт с FastAPI и PostgreSQL.",
            "education": [
                {
                    "institution": "Университет",
                    "degree": "Бакалавр",
                    "start_year": 2024,
                    "end_year": 2020,
                }
            ],
        },
    )

    assert response.status_code == 422


def test_pdf_endpoint_returns_pdf_after_generation() -> None:
    """Полный flow: POST → poll → GET PDF."""
    payload = {
        "vacancy_text": (
            "Middle Python Backend Developer. "
            "Build FastAPI APIs with PostgreSQL, Redis, Docker, SQLAlchemy and Pytest. "
            "3+ years of Python backend experience required."
        ),
        "full_name": "Иван Петров",
        "education": [
            {
                "institution": "Казанский федеральный университет",
                "degree": "Бакалавр",
                "field_of_study": "Программная инженерия",
                "start_year": 2017,
                "end_year": 2021,
            }
        ],
        "languages": [{"language": "Английский", "level": "B2"}],
    }
    resp = client.post("/api/v1/generations", json=payload)
    assert resp.status_code == 202, resp.text
    gen_id = resp.json()["generation_id"]

    # Ждём завершения (inline background task, max 60s)
    for _ in range(30):
        time.sleep(2)
        status_resp = client.get(f"/api/v1/generations/{gen_id}")
        assert status_resp.status_code == 200
        body = status_resp.json()
        if body["status"] == "completed":
            break
        if body["status"] == "failed":
            pytest.fail(f"Generation failed: {body.get('error')}")
    else:
        pytest.fail("Generation did not complete in 60 seconds")

    assert body["resume"]["header"]["name"] == "Иван Петров"
    assert body["resume"]["education"] == [
        "Бакалавр, Программная инженерия — Казанский федеральный университет, 2017–2021"
    ]
    assert body["resume"]["languages"] == ["Английский — B2 — выше среднего"]

    # Проверяем PDF endpoint
    pdf_resp = client.get(f"/api/v1/resumes/{gen_id}/pdf")
    assert pdf_resp.status_code == 200, f"PDF status: {pdf_resp.status_code}"
    assert "application/pdf" in pdf_resp.headers.get("content-type", ""), \
        f"Content-Type: {pdf_resp.headers.get('content-type')}"
    assert len(pdf_resp.content) > 500, f"PDF too small: {len(pdf_resp.content)} bytes"
