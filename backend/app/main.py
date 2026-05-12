"""FastAPI application entry point.

The backend is an API-only service. Static frontend assets are hosted
separately on Firebase Hosting (see frontend/firebase.json), so this app
no longer mounts the Vite build output.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import calculations


def create_app() -> FastAPI:
    app = FastAPI(
        title="Satellite RF Communications Calculator API",
        version="0.1.0",
        description="Backend API for common satellite RF link calculations.",
    )

    # CORS: allow local dev (Vite proxy + direct) and the production
    # Firebase Hosting origins. Update if the Firebase project changes.
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://satellite-rf-app.web.app",
        "https://satellite-rf-app.firebaseapp.com",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(calculations.router, prefix="/api")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
