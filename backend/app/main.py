"""FastAPI application factory for DocTongue.

Call :func:`create_app` to construct the app with CORS middleware and
all API routers registered under the configured ``api_prefix``.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.core.config import get_settings
from app.models.schemas import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        return HealthResponse(status="ok")

    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    return app


app = create_app()