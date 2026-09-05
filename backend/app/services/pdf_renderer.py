from __future__ import annotations

import logging
import os
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.schemas import ResumeDocument

logger = logging.getLogger(__name__)


def _register_cyrillic_fonts() -> tuple[str, str]:
    """Register portable Cyrillic fonts for the emergency ReportLab renderer."""
    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    regular_candidates = (
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / "DejaVuSans.ttf",
        windir / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    bold_candidates = (
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / "DejaVuSans-Bold.ttf",
        windir / "Fonts" / "arialbd.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    regular_path = next((path for path in regular_candidates if path.exists()), None)
    bold_path = next((path for path in bold_candidates if path.exists()), regular_path)
    if regular_path is None:
        logger.error("Cyrillic TTF font not found; ReportLab fallback may lose glyphs")
        return "Helvetica", "Helvetica-Bold"

    if "ResumeSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("ResumeSans", str(regular_path)))
        pdfmetrics.registerFont(TTFont("ResumeSansBold", str(bold_path)))
    return "ResumeSans", "ResumeSansBold"


class PdfRenderer:
    async def render(self, html: str, resume: ResumeDocument, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch()
                page = await browser.new_page(viewport={"width": 794, "height": 1123})
                await page.set_content(html, wait_until="networkidle")
                await page.evaluate("document.fonts.ready")
                await page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
                await browser.close()
        except Exception as exc:
            logger.warning(
                "Playwright PDF rendering failed; using ReportLab fallback: %s",
                exc,
            )
            self._render_with_reportlab(resume, output_path)
        return output_path

    def _render_with_reportlab(self, resume: ResumeDocument, output_path: Path) -> None:
        def safe(value: object) -> str:
            return escape(str(value or ""))

        regular_font, bold_font = _register_cyrillic_fonts()
        styles = getSampleStyleSheet()
        normal = ParagraphStyle(
            "ResumeNormal",
            parent=styles["Normal"],
            fontName=regular_font,
            fontSize=9,
            leading=12,
        )
        heading = ParagraphStyle(
            "ResumeHeading",
            parent=styles["Heading2"],
            fontName=bold_font,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f3d3e"),
            spaceBefore=8,
        )
        title = ParagraphStyle(
            "ResumeTitle",
            parent=styles["Title"],
            fontName=bold_font,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#172026"),
        )
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        contact_line = " | ".join(
            safe(resume.header.get(key))
            for key in ("city", "email", "phone", "telegram")
            if resume.header.get(key)
        )
        story = [
            Paragraph(safe(resume.header.get("name", "Кандидат")), title),
            Paragraph(safe(resume.target_position), normal),
            Paragraph(contact_line or "Контактные данные не указаны", normal),
            Spacer(1, 6),
            Paragraph("Профессиональный профиль", heading),
            Paragraph(safe(resume.summary), normal),
            Paragraph("Ключевые навыки", heading),
            Paragraph(
                "; ".join(
                    f"{safe(key)}: {', '.join(safe(item) for item in value)}"
                    for key, value in resume.skills.items()
                ),
                normal,
            ),
            Paragraph("Опыт работы", heading),
        ]
        for item in resume.experience:
            story.extend(
                [
                    Paragraph(f"{safe(item.company)} - {safe(item.role)}", heading),
                    Paragraph(
                        f"{safe(item.sector)} | {safe(item.location)} | {safe(item.dates)}",
                        normal,
                    ),
                    Paragraph(safe(item.company_description), normal),
                    Paragraph(safe(item.project_description), normal),
                    Paragraph(safe(item.team), normal),
                ]
            )
            for bullet in item.bullets:
                story.append(Paragraph(f"- {safe(bullet)}", normal))
            story.append(
                Paragraph(
                    f"Технологии: {', '.join(safe(technology) for technology in item.technologies)}",
                    normal,
                )
            )
        story.extend(
            [
                Paragraph("Образование", heading),
                Paragraph("; ".join(safe(item) for item in resume.education), normal),
                Paragraph("Языки", heading),
                Paragraph("; ".join(safe(item) for item in resume.languages), normal),
            ]
        )
        doc.build(story)

