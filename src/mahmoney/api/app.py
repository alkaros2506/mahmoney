from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mahmoney.api.routes import dashboard, expenses, health, imports
from mahmoney.ui.routes import router as ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="mahmoney",
        description="Personal expense tracking system",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(expenses.router, prefix="/api/v1")
    app.include_router(imports.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    # Static files
    static_dir = Path(__file__).parent.parent / "ui" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # UI routes
    app.include_router(ui_router)

    return app
