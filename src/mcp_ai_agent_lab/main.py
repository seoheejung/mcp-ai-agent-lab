from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .backend import register_diagnostics_routes
from .config import Settings
from .errors import ApplicationError
from .models import MultiAgentRunResult
from .multi_agent import Phase6MultiAgentRunner

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Backend Diagnostics — Phase 6 Multi-Agent")
    active_settings = settings or Settings.from_environment()
    app.state.phase6_runner = Phase6MultiAgentRunner(active_settings)

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

    @app.post(
        "/api/multi-agent/{experiment}/start",
        response_model=MultiAgentRunResult,
    )
    async def start_multi_agent(experiment: str) -> MultiAgentRunResult:
        if experiment not in {"explicit_handoff", "autonomous_decision"}:
            raise ApplicationError("Unknown multi-agent experiment")
        return await app.state.phase6_runner.start(experiment)

    @app.post(
        "/api/multi-agent/{run_id}/approve",
        response_model=MultiAgentRunResult,
    )
    async def approve_multi_agent(run_id: str) -> MultiAgentRunResult:
        return await app.state.phase6_runner.resume(run_id, "approved")

    @app.post(
        "/api/multi-agent/{run_id}/reject",
        response_model=MultiAgentRunResult,
    )
    async def reject_multi_agent(run_id: str) -> MultiAgentRunResult:
        return await app.state.phase6_runner.resume(run_id, "rejected")

    return app


app = create_app()
