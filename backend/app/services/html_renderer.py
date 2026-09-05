"""HTML рендерер резюме — Jinja2 + поддержка нескольких шаблонов."""
from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas import ResumeDocument

logger = logging.getLogger(__name__)

AVAILABLE_TEMPLATES = ("modern", "ats", "classic")
DEFAULT_TEMPLATE = "modern"

# Шрифты встроены в CSS как base64: Playwright рендерит PDF из инлайн-HTML,
# где внешние ссылки на fonts.gstatic.com не загружаются.
_FONTS_CSS_PATH = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "caldera-fonts.css"


class HtmlRenderer:
    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir
        # Создаём Jinja2 env для каждого шаблона лениво
        self._envs: dict[str, Environment] = {}
        self._fonts_css: str | None = None

    def _load_fonts_css(self) -> str:
        if self._fonts_css is None:
            try:
                self._fonts_css = _FONTS_CSS_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                logger.warning(
                    "Встроенные шрифты не найдены (%s); запустите scripts/fetch_fonts.py",
                    _FONTS_CSS_PATH,
                )
                self._fonts_css = ""
        return self._fonts_css

    def _get_env(self, template_name: str) -> Environment:
        if template_name not in self._envs:
            tmpl_dir = self.templates_dir / template_name
            if not tmpl_dir.exists():
                logger.warning(
                    "Шаблон '%s' не найден в %s, использую '%s'",
                    template_name,
                    self.templates_dir,
                    DEFAULT_TEMPLATE,
                )
                tmpl_dir = self.templates_dir / DEFAULT_TEMPLATE
                template_name = DEFAULT_TEMPLATE
            self._envs[template_name] = Environment(
                loader=FileSystemLoader(str(tmpl_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._envs[template_name]

    def render(
        self,
        resume: ResumeDocument,
        output_path: Path,
        template_name: str = DEFAULT_TEMPLATE,
    ) -> str:
        """Рендерит HTML резюме и сохраняет в output_path.

        Возвращает HTML-строку для последующего PDF-рендеринга.
        """
        if template_name not in AVAILABLE_TEMPLATES:
            logger.warning("Неизвестный шаблон '%s', использую 'modern'", template_name)
            template_name = DEFAULT_TEMPLATE

        env = self._get_env(template_name)
        template = env.get_template("resume.html")
        css_path = self.templates_dir / template_name / "style.css"

        css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
        css = f"{self._load_fonts_css()}\n{css}"

        html = template.render(resume=resume, css=css)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        logger.info("HTML rendered: template=%s path=%s", template_name, output_path)
        return html
