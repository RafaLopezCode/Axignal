"""CLI entry point for the AXIGNAL production runtime."""

from __future__ import annotations

from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, serve


def main() -> None:
    config = RuntimeConfig.from_env()
    runtime = build_runtime(config)
    serve(runtime)


if __name__ == "__main__":
    main()
