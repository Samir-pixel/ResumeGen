"""Тесты multi-template поддержки."""
from pathlib import Path

import pytest

from app.core.config import _DEFAULT_TEMPLATES
from app.schemas import ResumeDocument
from app.services.html_renderer import AVAILABLE_TEMPLATES, HtmlRenderer
from app.services.pdf_renderer import PdfRenderer


def _make_resume() -> ResumeDocument:
    return ResumeDocument(
        header={"name": "Ivan Petrov", "city": "Warsaw", "email": "i@p.com", "phone": "+48 500"},
        target_position="Middle Python Backend Developer",
        summary="Backend developer with 4 years of experience in Python services.",
        skills={"Backend": ["Python", "FastAPI"], "Data": ["PostgreSQL"]},
        experience=[],
        education=["BSc in CS — Warsaw University, 2021"],
        languages=["English — B2", "Russian — Native"],
    )


@pytest.mark.parametrize("template_name", AVAILABLE_TEMPLATES)
def test_html_renderer_renders_all_templates(tmp_path: Path, template_name: str) -> None:
    """Каждый шаблон должен рендериться без ошибок."""
    renderer = HtmlRenderer(_DEFAULT_TEMPLATES)
    resume = _make_resume()
    out = tmp_path / f"{template_name}.html"

    html = renderer.render(resume, out, template_name=template_name)

    assert out.exists(), f"HTML file not created for template '{template_name}'"
    assert len(html) > 200, f"HTML too short for template '{template_name}': {len(html)} chars"
    assert resume.header["name"] in html, "Candidate name not in HTML"
    assert resume.target_position in html, "Target position not in HTML"
    assert "Профессиональный профиль" in html
    assert "Опыт работы" in html
    assert "Образование" in html


def test_html_renderer_fallback_to_modern_on_unknown(tmp_path: Path) -> None:
    """Неизвестный шаблон → fallback на modern."""
    renderer = HtmlRenderer(_DEFAULT_TEMPLATES)
    resume = _make_resume()
    out = tmp_path / "unknown.html"

    html = renderer.render(resume, out, template_name="nonexistent_template")

    assert out.exists()
    assert len(html) > 200


def test_pdf_fallback_tolerates_missing_contact_fields(tmp_path: Path) -> None:
    """ReportLab fallback must not fail when an LLM omits optional header keys."""
    resume = _make_resume()
    resume.header = {"name": "Ivan & Petrov"}
    out = tmp_path / "fallback.pdf"

    PdfRenderer()._render_with_reportlab(resume, out)

    assert out.exists()
    assert out.stat().st_size > 1_000
