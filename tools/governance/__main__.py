"""``python -m tools.governance`` entry point.

Runs all deterministic governance checks, or a named subset.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.governance.checks import CHECKS


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="axignal-governance",
        description="Run deterministic AXIGNAL governance checks.",
    )
    parser.add_argument(
        "checks",
        nargs="*",
        help=f"checks to run (default: all). Available: {', '.join(sorted(CHECKS))}",
    )
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    selected = args.checks or sorted(CHECKS)

    unknown = [name for name in selected if name not in CHECKS]
    if unknown:
        sys.stderr.write(f"unknown check(s): {', '.join(unknown)}\n")
        return 2

    failed = False
    for name in selected:
        problems = CHECKS[name](root)
        if problems:
            failed = True
            sys.stdout.write(f"FAIL {name}\n")
            for problem in problems:
                sys.stdout.write(f"  - {problem}\n")
        else:
            sys.stdout.write(f"PASS {name}\n")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
