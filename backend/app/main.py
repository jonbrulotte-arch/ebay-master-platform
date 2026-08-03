from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="eBay Master Platform",
        description="eBay dropshipping business management platform",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    @application.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return application


app = create_app()
