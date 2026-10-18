from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Keep pytest fixtures outside the checkout and isolated per worktree."""
    if config.option.basetemp is not None:
        return
    checkout = config.rootpath.resolve()
    suffix = hashlib.sha256(str(checkout).encode("utf-8")).hexdigest()[:12]
    config.option.basetemp = str(Path(tempfile.gettempdir()) / f"axignal-pytest-{suffix}")
