from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    application = FastAPI(title="FullCRM API")
    application.state.settings = resolved_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.api_cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": resolved_settings.service_name,
            "environment": resolved_settings.app_env,
        }

    application.include_router(auth_router)

    return application


app = create_app()
