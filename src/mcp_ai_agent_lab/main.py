from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .agent_mcp import Phase4AgentMcpRunner
from .backend import register_diagnostics_routes
from .backend_client import DiagnosticsClient
from .config import Settings
from .errors import ApplicationError
from .models import AgentMcpComparisonResult
from .tools import FunctionTools

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Backend Diagnostics — Phase 4 Agent + MCP")
    active_settings = settings or Settings.from_environment()
    app.state.phase4_runner = Phase4AgentMcpRunner(
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

    @app.post("/api/agent-mcp/comparison", response_model=AgentMcpComparisonResult)
    async def compare_agent_mcp() -> AgentMcpComparisonResult:
        return await app.state.phase4_runner.run(
            "order-api의 응답이 느려졌어. 원인을 조사해줘."
        )

    return app


app = create_app()
