from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.ticket_replies import router as ticket_replies_router
from app.api.tickets import router as tickets_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.users import ensure_initial_admin

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with SessionLocal() as session:
        ensure_initial_admin(session)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ai_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(ticket_replies_router, prefix="/api")
app.include_router(users_router, prefix="/api")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
