from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .backend import register_diagnostics_routes
from .config import Settings
from .errors import ApplicationError
from .mcp_client import Phase3McpClient
from .models import McpVerificationResult

WEB_DIRECTORY = Path(__file__).resolve().parents[2] / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Backend Diagnostics — Phase 3 MCP Server")
    active_settings = settings or Settings.from_environment()
    app.state.phase3_mcp_client = Phase3McpClient(active_settings)

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

    @app.post("/api/mcp/verification", response_model=McpVerificationResult)
    async def verify_mcp() -> McpVerificationResult:
        return await app.state.phase3_mcp_client.verify()

    return app


app = create_app()
