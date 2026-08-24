from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .backend import register_diagnostics_routes
from .backend_client import DiagnosticsClient
from .config import Settings
from .errors import ApplicationError
from .models import DiagnosticRunResult, StreamingCheckResult
from .runner import ToolCallingRunner
from .tools import FunctionTools

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"


class DiagnosticRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Backend Diagnostics — Phase 1 Tool Calling")
    active_settings = settings or Settings.from_environment()
    app.state.diagnostic_runner = ToolCallingRunner(
        active_settings,
        FunctionTools(DiagnosticsClient(active_settings.backend_base_url)),
    )

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

    @app.post("/api/diagnostics", response_model=DiagnosticRunResult)
    async def run_diagnostics(request: DiagnosticRequest) -> DiagnosticRunResult:
        return await app.state.diagnostic_runner.run(request.question)

    @app.post("/api/streaming-check", response_model=StreamingCheckResult)
    async def streaming_check() -> StreamingCheckResult:
        return await app.state.diagnostic_runner.verify_streaming()

    return app


app = create_app()
