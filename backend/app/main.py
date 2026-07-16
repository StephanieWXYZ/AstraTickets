from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(auth_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
