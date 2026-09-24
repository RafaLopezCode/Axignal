"""AXIGNAL domain layer.

The innermost architecture layer. Domain modules model the canonical economic
world (AXIGLAND) and may import only the standard library and other ``domain``
packages. Domain MUST NOT import ``pipeline``, ``cognition``, ``apps`` or
``tools``.

Doctrine: MASTER §3 (AXIGLAND), §8 (demand-materialized graph), §15 (evidence),
§36 (conceptual data model).
"""

from __future__ import annotations

__all__: list[str] = []
