"""Cognitive provider adapters.

The ONLY place concrete model-provider SDKs may be imported. Adapters depend
inward through the ``CognitiveProvider`` interface and never write canonical
state.

Doctrine: MASTER §13.1, §13.2, §46.28.
"""

from __future__ import annotations

from cognition.providers.base import CognitiveProvider
from cognition.providers.echo import EchoProvider

__all__ = ["CognitiveProvider", "EchoProvider"]
