from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.analytics.routes import router as analytics_router
from app.auth.routes import router as auth_router
from app.ai.routes import router as ai_router
from app.communications.routes import router as communications_router
from app.crm.routes import router as crm_router
from app.config import Settings
from app.db.session import DatabaseNotConfiguredError, clear_session_cache, get_session_factory


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings: Settings = application.state.settings

    if settings.database_url:
        application.state.session_factory = get_session_factory(settings.database_url)

    try:
        yield
    finally:
        clear_session_cache()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    application = FastAPI(title="FullCRM API", lifespan=lifespan)
    application.state.settings = resolved_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.api_cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(DatabaseNotConfiguredError)
    def handle_database_not_configured(
        request: Request,
        error: DatabaseNotConfiguredError,
    ) -> JSONResponse:
        _ = request
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(error)},
        )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": resolved_settings.service_name,
            "environment": resolved_settings.app_env,
        }

    @application.get("/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/ready")
    def readiness(response: Response) -> dict[str, object]:
        if not resolved_settings.database_url:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "error",
                "checks": {"database": "not_configured"},
            }

        session_factory = getattr(application.state, "session_factory", None)

        if session_factory is None:
            session_factory = get_session_factory(resolved_settings.database_url)
            application.state.session_factory = session_factory

        try:
            with session_factory() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "error",
                "checks": {"database": "unavailable"},
            }

        return {
            "status": "ok",
            "checks": {"database": "ok"},
        }

    application.include_router(auth_router)
    application.include_router(crm_router)
    application.include_router(communications_router)
    application.include_router(ai_router)
    application.include_router(analytics_router)

    return application


app = create_app()
