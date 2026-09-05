"""Рендерит последнее резюме в PNG/PDF для визуальной проверки шаблона.

Запуск: python scripts/preview_resume.py [generation_id]
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.repositories.file_repository import FileGenerationRepository
from app.services.html_renderer import HtmlRenderer


async def main() -> None:
    settings = get_settings()
    storage = settings.generated_storage_dir
    repository = FileGenerationRepository(storage)

    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    else:
        runs = sorted(storage.glob("*.json"), key=os.path.getmtime)
        if not runs:
            print("Нет сохранённых генераций")
            return
        run_id = runs[-1].stem

    run = repository.get(run_id)
    if not run or not run.resume:
        print(f"Генерация {run_id} без резюме")
        return

    html_path = storage / "preview_resume.html"
    HtmlRenderer(settings.templates_dir).render(run.resume, html_path, "modern")

    png_path = storage / "preview_resume.png"
    header_path = storage / "preview_resume_header.png"
    pdf_path = storage / "preview_resume.pdf"

    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 794, "height": 1123}, device_scale_factor=2
        )
        await page.goto(html_path.as_uri(), wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        await page.screenshot(path=str(png_path), full_page=True)
        await page.locator(".hero").screenshot(path=str(header_path))
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        used_fonts = await page.evaluate(
            "getComputedStyle(document.querySelector('h1')).fontFamily"
        )
        await browser.close()

    print(f"generation : {run_id}")
    print(f"h1 font    : {used_fonts}")
    print(f"png        : {png_path}")
    print(f"header png : {header_path}")
    print(f"pdf        : {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


asyncio.run(main())
