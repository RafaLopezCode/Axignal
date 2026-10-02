"""Experimental Obscura adapter for P0-SOURCE-01D only.

The adapter intentionally cannot emit SourceObservation because Obscura v0.2.3
does not provide all provenance required by the production contract.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from application.source_acquisition.contracts import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
)


@dataclass(frozen=True)
class ExperimentalObscuraResult:
    request_id: str
    requested_uri: str
    rendered_html_ref: str | None
    rendered_html_sha256: str | None
    instrument_ref: str
    exit_code: int
    provenance_complete: bool
    blockers: tuple[str, ...]


class ObscuraExperimentalAdapter:
    INSTRUMENT_REF = "obscura:v0.2.3:experimental"

    def __init__(self, binary: Path) -> None:
        if not binary.is_file():
            raise FileNotFoundError(binary)
        self._binary = binary

    def acquire(
        self,
        request: SourceRequest,
        policy: SourceDispatchPolicy,
        *,
        output: Path,
        synthetic_allow_private_network: bool = False,
    ) -> ExperimentalObscuraResult:
        if policy.disposition is not DispatchDisposition.ALLOW:
            raise PermissionError("source policy denies acquisition")
        if request.policy_id != policy.policy_id:
            raise ValueError("request policy id mismatch")
        if request.policy_fingerprint != policy.fingerprint:
            raise ValueError("request policy fingerprint mismatch")

        command = [str(self._binary)]
        if synthetic_allow_private_network:
            command.append("--allow-private-network")
        command.extend(
            [
                "fetch",
                request.target_uri,
                "--dump",
                "html",
                "--timeout",
                str(max(1, (policy.timeout_ms + 999) // 1000)),
                "--output",
                str(output),
            ]
        )
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=(policy.timeout_ms / 1000) + 4,
            check=False,
        )
        fingerprint = None
        artifact_ref = None
        if output.exists():
            body = output.read_bytes()
            fingerprint = hashlib.sha256(body).hexdigest()
            artifact_ref = str(output)

        return ExperimentalObscuraResult(
            request_id=request.request_id,
            requested_uri=request.target_uri,
            rendered_html_ref=artifact_ref,
            rendered_html_sha256=fingerprint,
            instrument_ref=self.INSTRUMENT_REF,
            exit_code=completed.returncode,
            provenance_complete=False,
            blockers=(
                "peer IP is not available through the v0.2.3 browser boundary",
                "redirect-hop lineage is incomplete through the v0.2.3 browser boundary",
                "hard response/subresource byte cap is not enforced by the v0.2.3 CLI",
            ),
        )
