from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

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

    # --- Frontend static serving (for Docker / Cloud Run) ---

    # Path: /app/backend/app/main.py inside the container
    # parents[0] = app
    # parents[1] = backend
    # parents[2] = /app  (Docker WORKDIR)
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"

    if frontend_dist.exists():
        # In production/container: serve built Vite assets
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist / "assets"),
            name="assets",
        )

        @app.get("/", include_in_schema=False)
        async def serve_frontend():
            return FileResponse(frontend_dist / "index.html")
    else:
        # In local dev (using Vite dev server), dist usually doesn't exist.
        # This keeps "/" from breaking and nudges you to use :3000.
        @app.get("/", include_in_schema=False)
        async def frontend_not_built():
            return PlainTextResponse(
                "Frontend build not found.\n"
                "In development, use http://localhost:3000 for the Vite dev server.\n"
                "In production/Docker, run `npm run build` in frontend/ first.",
                status_code=200,
            )

    return app


app = create_app()
