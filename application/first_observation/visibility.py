from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

from application.first_observation.rights import ContentRights


def first_proof_live_deadline(
    proof: Mapping[str, Any],
    rights_for: Callable[[str], ContentRights],
) -> datetime | None:
    """Reevaluate an *originally governed* first proof's citation authority.

    Unregistered private observations keep the bounded baseline from ADR-0091;
    losing a prior registered grant cannot silently revert to that baseline.
    """
    recorded = proof.get("rights")
    if not isinstance(recorded, Mapping) or not recorded.get("basisRef"):
        return None
    website = proof.get("target", {}).get("website")
    if not isinstance(website, str) or not website:
        return None
    observed = datetime.fromisoformat(str(proof["observedAt"]))
    current = rights_for(website)
    if not current.reuse_permitted or current.basis_ref != recorded["basisRef"]:
        return observed
    return current.private_until(observed)


def withdraw_first_proof(proof: Mapping[str, Any], *, at: datetime) -> dict[str, Any]:
    """Fail closed at read and purge without erasing the historical envelope."""
    stripped = dict(proof)
    stripped["state"] = "SOURCE_UNAVAILABLE"
    stripped["firstProofReady"] = False
    stripped["attentionScopes"] = []
    stripped["capabilities"] = []
    stripped["discoveries"] = [
        {
            "kind": "SIGNIFICANT_UNKNOWN",
            "code": "CONTENT_RIGHTS_WITHDRAWN",
            "statement": "Previously observed website evidence is no longer authorized for display.",
            "epistemicState": "UNKNOWN",
            "sourceUrl": None,
            "excerpt": None,
            "observedAt": None,
            "detail": {},
        }
    ]
    stripped["contentExpiredAt"] = at.isoformat()
    return stripped
