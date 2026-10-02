"""Fail-closed environment configuration for the AXIGNAL production runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    environment: str
    bind_host: str
    port: int
    code_sha: str
    data_dir: Path
    web_root: Path
    first_proof_allowed_host: str | None = None
    containerized: bool = False

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        environment = os.getenv("AXIGNAL_ENV", "development").strip().lower()
        bind_host = os.getenv("AXIGNAL_BIND_HOST", "127.0.0.1").strip()
        port = int(os.getenv("AXIGNAL_PORT", "8765"))
        code_sha = os.getenv("AXIGNAL_CODE_SHA", "UNKNOWN").strip()
        data_raw = os.getenv("AXIGNAL_DATA_DIR", "").strip()
        web_raw = os.getenv("AXIGNAL_WEB_ROOT", "").strip()
        first_proof_allowed_host = (
            os.getenv("AXIGNAL_FIRST_PROOF_ALLOWED_HOST", "").strip().lower() or None
        )
        containerized = os.getenv("AXIGNAL_CONTAINERIZED", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }

        if not bind_host:
            raise ValueError("AXIGNAL_BIND_HOST cannot be empty")
        if not 1 <= port <= 65535:
            raise ValueError("AXIGNAL_PORT must be a valid TCP port")
        if not data_raw:
            raise ValueError("AXIGNAL_DATA_DIR is required")
        if not web_raw:
            raise ValueError("AXIGNAL_WEB_ROOT is required")
        if environment == "production" and code_sha == "UNKNOWN":
            raise ValueError("AXIGNAL_CODE_SHA is required in production")
        if (
            environment == "production"
            and bind_host not in {"127.0.0.1", "::1"}
            and not (containerized and bind_host == "0.0.0.0")
        ):
            raise ValueError(
                "production runtime must bind to loopback unless explicitly containerized"
            )

        data_dir = Path(data_raw).expanduser().resolve()
        web_root = Path(web_raw).expanduser().resolve()
        if not web_root.is_dir():
            raise ValueError("AXIGNAL_WEB_ROOT must exist and be a directory")
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            environment,
            bind_host,
            port,
            code_sha,
            data_dir,
            web_root,
            first_proof_allowed_host,
            containerized,
        )
