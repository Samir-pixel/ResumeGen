from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

_cors_origins = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.frontend_url.rstrip("/"),
}
_cors_origins.update(
    origin.strip().rstrip("/")
    for origin in settings.cors_origins.split(",")
    if origin.strip()
)

app = FastAPI(title="AI Resume Generator", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_cors_origins),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}

