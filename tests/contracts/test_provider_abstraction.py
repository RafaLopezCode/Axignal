"""Provider abstraction and non-canonical model output (MASTER §13, §14)."""

from __future__ import annotations

from cognition.jobs.model import CognitiveJob, JobKind
from cognition.providers.echo import EchoProvider
from cognition.router.router import ModelRouter, NoProviderAvailable
from domain.faxt.model import FAXT
from domain.organizations.model import Organization
from domain.relationships.model import ObservedRelationship


def _job() -> CognitiveJob:
    return CognitiveJob(id="job-1", kind=JobKind.ENTITY_RESOLUTION, instruction="resolve ACME")


def test_router_routes_to_registered_provider() -> None:
    router = ModelRouter([EchoProvider()])
    result = router.route(_job())
    assert result.provider == "echo"
    assert result.payload["echo"] == "resolve ACME"


def test_router_without_providers_fails_closed() -> None:
    router = ModelRouter()
    try:
        router.route(_job())
    except NoProviderAvailable:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("empty router did not fail closed")


def test_provider_output_is_never_canonical_truth() -> None:
    result = EchoProvider().complete(_job())
    assert result.is_canonical_truth is False
    assert not isinstance(result, (FAXT, ObservedRelationship, Organization))
