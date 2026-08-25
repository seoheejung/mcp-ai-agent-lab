from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .backend import register_diagnostics_routes
from .config import Settings
from .errors import ApplicationError
from .human_approval import Phase5HumanApprovalRunner
from .models import ApprovalRunResult

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Backend Diagnostics — Phase 5 Human Approval")
    active_settings = settings or Settings.from_environment()
    app.state.phase5_runner = Phase5HumanApprovalRunner(active_settings)

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_, error: ApplicationError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": str(error), "error_type": error.error_type},
        )

    register_diagnostics_routes(app)
    app.mount("/static", StaticFiles(directory=WEB_DIRECTORY), name="static")

    @app.get("/", include_in_schema=False)
    async def web_application() -> FileResponse:
        return FileResponse(WEB_DIRECTORY / "index.html")

    @app.post("/api/human-approval/start", response_model=ApprovalRunResult)
    async def start_human_approval() -> ApprovalRunResult:
        return await app.state.phase5_runner.start()

    @app.post(
        "/api/human-approval/{run_id}/approve",
        response_model=ApprovalRunResult,
    )
    async def approve_human_approval(run_id: str) -> ApprovalRunResult:
        return await app.state.phase5_runner.resume(run_id, "approved")

    @app.post(
        "/api/human-approval/{run_id}/reject",
        response_model=ApprovalRunResult,
    )
    async def reject_human_approval(run_id: str) -> ApprovalRunResult:
        return await app.state.phase5_runner.resume(run_id, "rejected")

    return app


app = create_app()
