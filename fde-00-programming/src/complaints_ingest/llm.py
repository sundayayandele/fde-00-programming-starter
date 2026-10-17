"""Provider-agnostic chat client for OpenAI-compatible endpoints.

Mistral is the default. DeepSeek, OpenAI, Qwen, Kimi and self-hosted vLLM are
switched in through config/providers.yaml, without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml


class LLMConfigError(RuntimeError):
    """Raised when the provider configuration is missing or unusable."""


class DataResidencyError(RuntimeError):
    """Raised when regulated data would be sent to a provider not allowed to receive it."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key_env: str
    regulated_data_allowed: bool
    models: dict[str, str] = field(default_factory=dict)

    def model_for(self, role: str) -> str:
        if role not in self.models:
            raise LLMConfigError(f"Provider '{self.name}' has no model for role '{role}'")
        model = self.models[role]
        if model == "PIN_AT_BUILD_TIME":
            raise LLMConfigError(
                f"Model for role '{role}' on provider '{self.name}' is not pinned yet. "
                "Set it in config/providers.yaml and record it in an ADR."
            )
        return model


def load_providers(path: str | Path) -> tuple[str, dict[str, Provider]]:
    path = Path(path)
    if not path.exists():
        raise LLMConfigError(f"Providers file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    providers = {
        name: Provider(
            name=name,
            base_url=spec["base_url"].rstrip("/"),
            api_key_env=spec["api_key_env"],
            regulated_data_allowed=bool(spec.get("regulated_data_allowed", False)),
            models=dict(spec.get("models", {})),
        )
        for name, spec in (raw.get("providers") or {}).items()
    }
    default = raw.get("default", "mistral")
    if default not in providers:
        raise LLMConfigError(f"Default provider '{default}' is not defined")
    return default, providers


class LLMClient:
    """Minimal chat-completions client. One instance per provider."""

    def __init__(
        self,
        provider: Provider,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        api_key = os.getenv(provider.api_key_env, "")
        if not api_key:
            raise LLMConfigError(f"Environment variable {provider.api_key_env} is not set")
        self.provider = provider
        self._http = httpx.Client(
            base_url=provider.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            transport=transport,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        role: str = "default",
        contains_regulated_data: bool = False,
        **params: Any,
    ) -> str:
        if contains_regulated_data and not self.provider.regulated_data_allowed:
            raise DataResidencyError(
                f"Provider '{self.provider.name}' may not receive regulated data. "
                "Use mistral or selfhosted for this request."
            )
        payload = {"model": self.provider.model_for(role), "messages": messages, **params}
        response = self._http.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._http.close()


def client_for(provider_name: str | None = None, providers_file: str | Path | None = None,
               **kwargs: Any) -> LLMClient:
    from complaints_ingest.config import get_settings

    settings = get_settings()
    default, providers = load_providers(providers_file or settings.llm_providers_file)
    name = provider_name or settings.llm_provider or default
    if name not in providers:
        raise LLMConfigError(f"Unknown provider '{name}'. Known: {sorted(providers)}")
    return LLMClient(providers[name], timeout=settings.llm_timeout_seconds, **kwargs)
