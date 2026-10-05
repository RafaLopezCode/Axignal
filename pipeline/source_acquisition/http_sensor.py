"""Governed deterministic HTTP source sensor."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urljoin

from application.source_acquisition import (
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
)
from pipeline.source_acquisition.artifacts import ContentAddressedArtifactStore
from pipeline.source_acquisition.http_transport import (
    PinnedHttpTransport,
    RawHttpResponse,
    SourceDeadlineExceeded,
)
from pipeline.source_acquisition.policy import PublicSourcePolicyGate, SourcePolicyRejected

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class HttpSourceSensor:
    """Policy-first, bounded, direct HTTP observation with no truth authority."""

    def __init__(
        self,
        *,
        policy_gate: PublicSourcePolicyGate,
        transport: PinnedHttpTransport,
        artifacts: ContentAddressedArtifactStore,
        clock: Callable[[], datetime] | None = None,
        monotonic_ns: Callable[[], int] | None = None,
    ) -> None:
        self._policy_gate = policy_gate
        self._transport = transport
        self._artifacts = artifacts
        self._clock = clock or (lambda: datetime.now(UTC))
        self._monotonic_ns = monotonic_ns or time.monotonic_ns

    def observe(
        self,
        request: SourceRequest,
        policy: SourceDispatchPolicy,
    ) -> SourceObservation:
        if request.policy_id != policy.policy_id:
            raise SourcePolicyRejected("request_policy_id_mismatch")
        if request.policy_fingerprint != policy.fingerprint:
            raise SourcePolicyRejected("request_policy_fingerprint_mismatch")

        requested_uri = request.target_uri
        current_uri = requested_uri
        redirect_chain: list[str] = [requested_uri]
        peer_ips: list[str] = []
        final_response: RawHttpResponse | None = None
        failure_state: str | None = None
        final_uri = requested_uri
        deadline_ns = self._monotonic_ns() + policy.timeout_ms * 1_000_000

        for hop in range(policy.max_redirects + 1):
            if self._monotonic_ns() >= deadline_ns:
                failure_state = "deadline_exceeded"
                break

            try:
                resolved = self._policy_gate.resolve(current_uri, policy)
            except SourcePolicyRejected:
                if hop == 0:
                    raise
                failure_state = "redirect_policy_rejected"
                break

            if self._monotonic_ns() >= deadline_ns:
                failure_state = "deadline_exceeded"
                break

            if redirect_chain[-1] != resolved.uri:
                redirect_chain.append(resolved.uri)
            final_uri = resolved.uri

            remaining_ns = deadline_ns - self._monotonic_ns()
            if remaining_ns <= 0:
                failure_state = "deadline_exceeded"
                break
            remaining_ms = max(1, (remaining_ns + 999_999) // 1_000_000)

            try:
                response = self._transport.fetch(
                    resolved,
                    timeout_ms=remaining_ms,
                    max_response_bytes=policy.max_response_bytes,
                )
            except SourceDeadlineExceeded:
                failure_state = "deadline_exceeded"
                break
            except OSError as exc:
                failure_state = f"transport_error:{type(exc).__name__}"
                break

            final_response = response
            peer_ips.append(response.peer_ip)
            if response.failure_state is not None:
                failure_state = response.failure_state
                break

            if response.status not in _REDIRECT_STATUSES:
                if response.status >= 400:
                    failure_state = f"http_{response.status}"
                break

            location = response.header("Location")
            if not location:
                failure_state = "redirect_missing_location"
                break
            if hop >= policy.max_redirects:
                failure_state = "redirect_limit_exceeded"
                break
            current_uri = urljoin(resolved.uri, location)

        retrieved_at = self._clock()
        if retrieved_at.tzinfo is None:
            raise ValueError("source sensor clock must return timezone-aware datetimes")
        retrieved_at = retrieved_at.astimezone(UTC)

        body = final_response.body if final_response is not None else b""
        body_ref = self._artifacts.put_bytes(body) if body else None
        body_fingerprint = f"sha256:{hashlib.sha256(body).hexdigest()}" if body else None
        status = final_response.status if final_response is not None else None
        content_type = final_response.header("Content-Type") if final_response is not None else None
        envelope = {
            "schema": "axignal.source-observation/0.2",
            "request": {
                "request_id": request.request_id,
                "subject_id": request.subject_id,
                "observation_slot": request.observation_slot,
                "requested_uri": redirect_chain[0],
                "source_type": request.source_type,
            },
            "policy": {
                "policy_id": policy.policy_id,
                "policy_fingerprint": policy.fingerprint,
                "decision_basis": policy.decision_basis,
                "disposition": policy.disposition.value,
                "targets": [
                    {
                        "host": target.host,
                        "path_prefix": target.path_prefix,
                        "schemes": list(target.schemes),
                    }
                    for target in policy.targets
                ],
                "max_response_bytes": policy.max_response_bytes,
                "timeout_ms": policy.timeout_ms,
                "max_redirects": policy.max_redirects,
            },
            "instrument_ref": self._transport.instrument_ref,
            "retrieved_at": retrieved_at.isoformat(),
            "final_uri": final_uri,
            "redirect_chain": redirect_chain,
            "peer_ips": peer_ips,
            "http_status": status,
            "content_type": content_type,
            "body_fingerprint": body_fingerprint,
            "body_artifact_ref": body_ref,
            "failure_state": failure_state,
        }
        envelope_ref = self._artifacts.put_json(envelope)
        observation_fingerprint = f"sha256:{ContentAddressedArtifactStore.digest(envelope_ref)}"

        return SourceObservation(
            request_id=request.request_id,
            subject_id=request.subject_id,
            observation_slot=request.observation_slot,
            requested_uri=redirect_chain[0],
            final_uri=final_uri,
            retrieved_at=retrieved_at,
            http_status=status,
            content_type=content_type,
            body_fingerprint=body_fingerprint,
            body_artifact_ref=body_ref,
            raw_observation_ref=envelope_ref,
            observation_fingerprint=observation_fingerprint,
            instrument_ref=self._transport.instrument_ref,
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            redirect_chain=tuple(redirect_chain),
            peer_ips=tuple(peer_ips),
            failure_state=failure_state,
        )
