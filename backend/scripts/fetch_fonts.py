"""Скачивает Oswald + Manrope с Google Fonts и собирает самодостаточный CSS.

Шрифты встраиваются в CSS как base64 data-URI: Playwright рендерит PDF из
инлайн-HTML без сетевого доступа, поэтому внешние ссылки на fonts.gstatic.com
не успевают (или не могут) загрузиться.

Запуск: python scripts/fetch_fonts.py
"""
from __future__ import annotations

import base64
import re
import urllib.request
from pathlib import Path

FONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Manrope:wght@500;700&family=Oswald:wght@600;700&display=swap"
)
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
# Резюме на русском с английскими названиями технологий — этих двух наборов хватает.
WANTED_SUBSETS = ("cyrillic", "latin")

OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "caldera-fonts.css"

_FACE_RE = re.compile(
    r"/\* (?P<subset>[\w-]+) \*/\s*@font-face \{(?P<body>.*?)\}",
    re.DOTALL,
)


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": CHROME_UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main() -> None:
    source_css = _get(FONTS_CSS_URL).decode("utf-8")
    faces: list[str] = []

    for match in _FACE_RE.finditer(source_css):
        if match.group("subset") not in WANTED_SUBSETS:
            continue
        body = match.group("body")
        url_match = re.search(r"src: url\((?P<url>[^)]+)\)", body)
        if not url_match:
            continue

        encoded = base64.b64encode(_get(url_match.group("url"))).decode("ascii")
        inlined = re.sub(
            r"src: url\([^)]+\) format\('woff2'\);",
            f"src: url(data:font/woff2;base64,{encoded}) format('woff2');",
            body,
        )
        faces.append(f"@font-face {{{inlined}}}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    header = "/* Сгенерировано scripts/fetch_fonts.py — не редактировать вручную. */\n"
    OUTPUT.write_text(header + "\n".join(faces), encoding="utf-8")
    print(f"{len(faces)} font faces -> {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
