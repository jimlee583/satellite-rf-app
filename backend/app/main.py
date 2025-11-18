from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import calculations


def create_app() -> FastAPI:
    app = FastAPI(
        title="Satellite RF Communications Calculator API",
        version="0.1.0",
        description="Backend API for common satellite RF link calculations.",
    )

    # CORS – allow local frontend during development
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(calculations.router, prefix="/api")

    return app


app = create_app()


