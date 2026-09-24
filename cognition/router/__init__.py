"""Model routing.

Doctrine: MASTER §13.1 (ModelRouter), §13.2 (model swap test), §13.3 (model
upgrade test).
"""

from __future__ import annotations

from cognition.router.router import ModelRouter, NoProviderAvailable

__all__ = ["ModelRouter", "NoProviderAvailable"]
