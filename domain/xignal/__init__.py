"""XIGNAL: persistent observation allocation.

"Xignal a company" assigns persistent computational observation. It does not
create a profile, claim a company, or grant authority to configure canonical
truth. This package must not import ``domain.organizations`` and must not expose
any Organization mutation.

Doctrine: MASTER §4.4, §7, §26, §32, §46.5, §46.14.
"""

from __future__ import annotations

from domain.xignal.observation_seed import (
    ObservationSeed,
    ObservationStatus,
    XignalError,
)

__all__ = ["ObservationSeed", "ObservationStatus", "XignalError"]
