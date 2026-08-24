from __future__ import annotations

import os
from dataclasses import dataclass

from .errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    backend_base_url: str
    openai_api_key: str | None
    openai_model: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            backend_base_url=os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL"),
        )

    def require_openai(self) -> tuple[str, str]:
        if not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is not configured")
        if not self.openai_model:
            raise ConfigurationError("OPENAI_MODEL is not configured")
        return self.openai_api_key, self.openai_model
