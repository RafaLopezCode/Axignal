"""Every setting the runtime reads must be declared, or the configuration file silently drops it.

2026-10-18: search ranking (spec 091) and web research (spec 098) read keys the subscriber
configuration ignored, so both stayed off in production with their keys mounted.
"""

from __future__ import annotations

import re
from pathlib import Path

from tools.runtime.subscriber_configuration import _KEYS

RUNTIME = Path(__file__).resolve().parents[2] / "tools" / "runtime"


def test_every_key_the_runtime_reads_is_declared() -> None:
    read: set[str] = set()
    for path in RUNTIME.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        read |= set(re.findall(r'values\.get\(\s*"(AXIGNAL_[A-Z0-9_]+)"', source))
        for constant, key in re.findall(r'^([A-Z_]+) = "(AXIGNAL_[A-Z0-9_]+)"', source, re.M):
            if re.search(r"values\.get\(\s*" + constant + r"\b", source):
                read.add(key)
    assert read, "the scan found no settings: the pattern is stale"
    assert sorted(read - _KEYS) == []
