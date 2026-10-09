"""Governed website GETs for First Observation, through the existing HTTP sensor.

The dispatch policy is limited to the website's own host (bare and ``www.``), with a
bounded response size, timeout and redirect budget. The sensor's policy gate resolves
and pins public addresses (no private hosts), and every response is kept as a
content-addressed artifact with its envelope: provenance once, reused many times.
"""

from __future__ import annotations

import hashlib
from urllib.parse import urlsplit

from application.first_observation.service import FetchedResource
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
    SourceTargetRule,
)
from pipeline.source_acquisition.artifacts import ContentAddressedArtifactStore
from pipeline.source_acquisition.http_sensor import HttpSourceSensor
from pipeline.source_acquisition.policy import SourcePolicyRejected

DECISION_BASIS = (
    "Subscriber-directed attention to a public website (spec 063, ADR-0091): robots.txt "
    "honoured before any page, bounded GETs on the site's own host, no authentication, "
    "no anti-bot bypass."
)


class GovernedSiteFetcher:
    def __init__(
        self,
        *,
        sensor: HttpSourceSensor,
        artifacts: ContentAddressedArtifactStore,
        max_response_bytes: int = 1_500_000,
        timeout_ms: int = 8_000,
        max_redirects: int = 3,
    ) -> None:
        self._sensor = sensor
        self._artifacts = artifacts
        self._max_bytes = max_response_bytes
        self._timeout_ms = timeout_ms
        self._max_redirects = max_redirects

    def policy_for(self, host: str) -> SourceDispatchPolicy:
        bare = host.lower().removeprefix("www.")
        return SourceDispatchPolicy(
            policy_id=f"first-observation-website:{bare}",
            disposition=DispatchDisposition.ALLOW,
            decision_basis=DECISION_BASIS,
            targets=(
                SourceTargetRule(bare, "/", ("https", "http")),
                SourceTargetRule("www." + bare, "/", ("https", "http")),
            ),
            max_response_bytes=self._max_bytes,
            timeout_ms=self._timeout_ms,
            max_redirects=self._max_redirects,
        )

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        host = urlsplit(url).hostname or ""
        policy = self.policy_for(host)
        request = SourceRequest(
            request_id="fo-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
            subject_id="site:" + host.lower().removeprefix("www."),
            observation_slot=slot,
            target_uri=url,
            source_type="PUBLIC_WEBSITE",
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            policy_version=policy.policy_version,
        )
        try:
            observed = self._sensor.observe(request, policy)
        except SourcePolicyRejected as error:
            return _refused(url, f"POLICY_REJECTED:{error}")
        except (OSError, ValueError) as error:
            return _refused(url, f"SENSOR:{type(error).__name__}")
        body = (
            None
            if observed.body_artifact_ref is None
            else self._artifacts.read(observed.body_artifact_ref)
        )
        if observed.body_artifact_ref is not None and not retain_body:
            # ADR-0015: raw text retention is not automatic. The envelope (URLs, status,
            # fingerprints) stays as metadata; the body exists only for this run.
            self._artifacts.discard(observed.body_artifact_ref)
        return FetchedResource(
            requested_url=url,
            final_url=observed.final_uri,
            observed_at=observed.retrieved_at,
            status=observed.http_status,
            content_type=observed.content_type,
            body=body,
            content_fingerprint=observed.body_fingerprint,
            artifact_ref=observed.raw_observation_ref,
            requests=len(observed.peer_ips),  # one per request actually sent
            failure=observed.failure_state,
        )


def _refused(url: str, failure: str) -> FetchedResource:
    from datetime import UTC, datetime

    return FetchedResource(
        requested_url=url,
        final_url=url,
        observed_at=datetime.now(UTC),
        status=None,
        content_type=None,
        body=None,
        content_fingerprint=None,
        artifact_ref=None,
        requests=0,
        failure=failure,
    )
