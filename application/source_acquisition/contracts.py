"""Provider-neutral contracts for governed source acquisition."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_SLOT = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("source-acquisition identity and policy values must be non-empty")


class DispatchDisposition(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class SourceTargetRule:
    """Exact host plus bounded path/scheme space authorized by source policy."""

    host: str
    path_prefix: str = "/"
    schemes: tuple[str, ...] = ("https",)

    def __post_init__(self) -> None:
        _required(self.host, self.path_prefix)
        if not self.path_prefix.startswith("/"):
            raise ValueError("source target path prefix must start with '/'")
        if not self.schemes or any(scheme not in {"http", "https"} for scheme in self.schemes):
            raise ValueError("source target schemes must be a non-empty http/https set")
        if len(set(self.schemes)) != len(self.schemes):
            raise ValueError("source target schemes must be unique")


@dataclass(frozen=True, slots=True)
class SourceDispatchPolicy:
    """Pre-dispatch authority. Acquisition cannot create or widen this policy."""

    policy_id: str
    disposition: DispatchDisposition
    decision_basis: str
    targets: tuple[SourceTargetRule, ...]
    max_response_bytes: int = 2_000_000
    timeout_ms: int = 5_000
    max_redirects: int = 3
    policy_version: str = "1"

    def __post_init__(self) -> None:
        _required(self.policy_id, self.policy_version, self.decision_basis)
        if self.disposition is DispatchDisposition.ALLOW and not self.targets:
            raise ValueError("allowed source policy requires at least one bounded target")
        if self.max_response_bytes < 1 or self.max_response_bytes > 20_000_000:
            raise ValueError("source response budget must be between 1 byte and 20 MB")
        if self.timeout_ms < 100 or self.timeout_ms > 30_000:
            raise ValueError("source timeout must be between 100 ms and 30 s")
        if self.max_redirects < 0 or self.max_redirects > 10:
            raise ValueError("source redirect budget must be between 0 and 10")

    @property
    def fingerprint(self) -> str:
        payload = {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "disposition": self.disposition.value,
            "decision_basis": self.decision_basis,
            "targets": [
                {
                    "host": target.host.rstrip(".").lower(),
                    "path_prefix": target.path_prefix,
                    "schemes": target.schemes,
                }
                for target in self.targets
            ],
            "max_response_bytes": self.max_response_bytes,
            "timeout_ms": self.timeout_ms,
            "max_redirects": self.max_redirects,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceRequest:
    request_id: str
    subject_id: str
    observation_slot: str
    target_uri: str
    source_type: str
    policy_id: str
    policy_fingerprint: str
    policy_version: str = "1"

    def __post_init__(self) -> None:
        _required(
            self.request_id,
            self.subject_id,
            self.observation_slot,
            self.target_uri,
            self.source_type,
            self.policy_id,
            self.policy_fingerprint,
            self.policy_version,
        )
        if not _SLOT.fullmatch(self.observation_slot):
            raise ValueError("observation slot must be a stable lowercase identifier")


@dataclass(frozen=True, slots=True)
class SourceObservation:
    """Acquisition outcome with exact lineage; never canonical truth."""

    request_id: str
    subject_id: str
    observation_slot: str
    requested_uri: str
    final_uri: str
    retrieved_at: datetime
    http_status: int | None
    content_type: str | None
    body_fingerprint: str | None
    body_artifact_ref: str | None
    raw_observation_ref: str
    observation_fingerprint: str
    instrument_ref: str
    policy_id: str
    policy_fingerprint: str
    redirect_chain: tuple[str, ...]
    peer_ips: tuple[str, ...]
    failure_state: str | None
    policy_version: str = "1"

    def __post_init__(self) -> None:
        _required(
            self.request_id,
            self.subject_id,
            self.observation_slot,
            self.requested_uri,
            self.final_uri,
            self.raw_observation_ref,
            self.observation_fingerprint,
            self.instrument_ref,
            self.policy_id,
            self.policy_fingerprint,
            self.policy_version,
        )
        if self.retrieved_at.tzinfo is None:
            raise ValueError("source retrieval time must be timezone-aware")
        if not self.redirect_chain or self.redirect_chain[0] != self.requested_uri:
            raise ValueError(
                "source observation must retain the requested URI as redirect-chain root"
            )
        if self.redirect_chain[-1] != self.final_uri:
            raise ValueError("source observation final URI must close the redirect chain")
        if (self.body_fingerprint is None) != (self.body_artifact_ref is None):
            raise ValueError("source body fingerprint and artifact reference must coexist")
        if self.http_status is not None and not self.peer_ips:
            raise ValueError("network response requires the connected peer IP")
        if self.http_status is None and self.failure_state is None:
            raise ValueError("source observation without HTTP status requires an explicit failure")
