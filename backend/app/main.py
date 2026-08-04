import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import api_router
from app.config import settings
from app.database import async_session

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    application = FastAPI(
        title="eBay Master Platform",
        description="eBay dropshipping business management platform",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("DB integrity error for %s %s: %s", request.method, request.url, exc.orig)
        return JSONResponse(
            status_code=409,
            content={"detail": "Resource already exists or constraint violation"},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception [%s] for %s %s",
            getattr(request.state, "request_id", "-"),
            request.method,
            request.url,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    application.include_router(api_router)

    @application.get("/health")
    async def health_check():
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        healthy = db_status == "healthy"
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={
                "status": "healthy" if healthy else "degraded",
                "database": db_status,
                "environment": settings.environment,
            },
        )

    return application


app = create_app()
