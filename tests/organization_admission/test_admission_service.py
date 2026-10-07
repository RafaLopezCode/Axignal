"""Spec 052: locator → governed identity → canonical Organization (or nothing)."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.organization_admission.locator import LocatorError, parse_locator
from application.organization_admission.service import (
    AdmissionStatus,
    AdmittedProposition,
    IdentityConflictError,
    OrganizationAdmissionService,
    PreparedAdmission,
    RegistryIdentityRecord,
    UnavailableRegistrySource,
    organization_id_for,
    prepare_admission,
)
from application.subscriber_portfolio.models import (
    OrganizationIdentityPending,
    OrganizationIdentityRejected,
)
from domain.evidence.admission import EvidenceAdmissionRequired, SourceAuthority
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.entity_resolution.organization_store import (
    OrganizationMaterializationError,
    SqliteCanonicalOrganizationStore,
)
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei

SOLAR = lei("SOLARTEC0000000001")
ACME_ONE = lei("ACMEONE00000000001")
ACME_TWO = lei("ACMETWO00000000002")


def _store(root: Path) -> SqliteCanonicalOrganizationStore:
    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    return SqliteCanonicalOrganizationStore(
        root / "canonical-organizations.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        governance=SqliteIdentityGovernanceStore(root / "identity-governance.sqlite3"),
    )


def _artifacts(root: Path) -> ContentAddressedArtifactStore:
    return ContentAddressedArtifactStore(root / "artifacts")


def _count(root: Path, table: str = "canonical_legal_identities") -> int:
    path = root / "canonical-organizations.sqlite3"
    if not path.exists():
        return 0
    with sqlite3.connect(path) as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _solartec(root: Path) -> RegistryIdentityRecord:
    return entity(
        _artifacts(root),
        legal_name="Solartec Energía SL",
        lei_value=SOLAR,
        websites=("https://www.solartec.example.com/",),
    )


# --- Locator ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("", "INVALID_LOCATOR"),
        ("x" * 2049, "INVALID_LOCATOR"),
        ("A", "NAME_TOO_SHORT"),
        ("org:id:abc", "INTERNAL_IDENTIFIER_NOT_ACCEPTED"),
        ("focus_0123", "INTERNAL_IDENTIFIER_NOT_ACCEPTED"),
        ("ops@solartec.example.com", "EMAIL_NOT_ACCEPTED"),
        ("https://user:pw@solartec.example.com/", "CREDENTIALS_IN_URL"),
        ("http://127.0.0.1/", "PUBLIC_HOSTNAME_REQUIRED"),
        ("https://localhost/", "PUBLIC_HOSTNAME_REQUIRED"),
        ("https://intranet.internal/", "PUBLIC_HOSTNAME_REQUIRED"),
        ("ftp://solartec.example.com/", "UNSUPPORTED_URL_SCHEME"),
        ("https://a.example.com https://b.example.com", "MULTIPLE_WEBSITES"),
        ("SOLARTEC000000000199", "INVALID_LEI_CHECKSUM"),
        ("Solar‮tec", "CONTROL_CHARACTERS"),
    ],
)
def test_invalid_locators_are_rejected_with_stable_codes(raw: str, code: str) -> None:
    with pytest.raises(LocatorError) as exc:
        parse_locator(raw)
    # The error carries only the stable code, never the submitted text.
    assert exc.value.code == code and str(exc.value) == code


def test_locator_classifies_name_website_and_lei_without_trusting_them() -> None:
    both = parse_locator("Solartec Energía SL\nhttps://www.solartec.example.com/")
    assert (both.name, both.domain, both.identifier) == (
        "Solartec Energía SL",
        "solartec.example.com",
        None,
    )
    assert parse_locator("Acme S.L").domain is None  # legal suffix, not a website
    assert parse_locator(f"LEI {SOLAR}").identifier is not None
    assert parse_locator("solartec.example.com").domain == "solartec.example.com"


# --- Resolution and admission ---------------------------------------------------------


def test_new_identity_is_admitted_once_then_reused_after_restart(tmp_path: Path) -> None:
    registry = ControlledRegistry([_solartec(tmp_path)])
    service = OrganizationAdmissionService(_store(tmp_path), registry)
    first = service.decide("Solartec Energía SL")
    assert first.status is AdmissionStatus.ADMITTED_NEW and first.organization is not None
    assert first.organization.id == organization_id_for("LEI", "GLEIF", SOLAR)
    assert first.organization.canonical_name == "Solartec Energía SL"  # exact admitted name
    # Restart: a fresh process resolves it from the canonical store, not the source.
    restarted = OrganizationAdmissionService(_store(tmp_path), registry)
    calls = registry.calls
    for locator in (
        "solartec energía sl",
        "https://solartec.example.com",
        "www.solartec.example.com",
        f"LEI {SOLAR}",
        "Solartec Energía SL https://solartec.example.com/",
    ):
        again = restarted.decide(locator)
        assert again.status is AdmissionStatus.RESOLVED_EXISTING, locator
        assert again.organization == first.organization
    assert registry.calls == calls
    assert _count(tmp_path) == 1
    assert _count(tmp_path, "canonical_identifiers") == 1
    assert _count(tmp_path, "canonical_websites") == 1


def test_provenance_of_every_key_is_preserved(tmp_path: Path) -> None:
    service = OrganizationAdmissionService(
        _store(tmp_path), ControlledRegistry([_solartec(tmp_path)])
    )
    service.decide(f"LEI {SOLAR}")
    with sqlite3.connect(tmp_path / "canonical-organizations.sqlite3") as connection:
        connection.row_factory = sqlite3.Row
        legal = connection.execute("SELECT * FROM canonical_legal_identities").fetchone()
        key = connection.execute("SELECT * FROM canonical_identifiers").fetchone()
        site = connection.execute("SELECT * FROM canonical_websites").fetchone()
    for row in (legal, key, site):
        assert row["evidence_ref"].startswith("evidence:registry:")
        assert row["policy_id"] == "predicate-legal-identity:v1"
        assert row["observed_at"].startswith("2026-10-07T09:00")
    assert (key["scheme"], key["authority"], key["value"]) == ("LEI", "GLEIF", SOLAR)
    assert site["domain"] == "solartec.example.com"


def test_unknown_identity_stays_pending_and_writes_nothing(tmp_path: Path) -> None:
    for source, reason in (
        (UnavailableRegistrySource(), "IDENTITY_SOURCE_UNAVAILABLE"),
        (ControlledRegistry([]), "NOT_FOUND_IN_IDENTITY_SOURCE"),
    ):
        service = OrganizationAdmissionService(_store(tmp_path), source)
        for locator in ("Unknown Example SL", "https://unknown.example.com/"):
            outcome = service.decide(locator)
            assert outcome.status is AdmissionStatus.IDENTITY_PENDING
            assert outcome.reason_code == reason and outcome.organization is None
            resolved = service.resolve(locator)
            assert isinstance(resolved, OrganizationIdentityPending)  # UNKNOWN, not false
    assert _count(tmp_path) == 0


def test_url_the_registry_does_not_attest_is_not_attributed(tmp_path: Path) -> None:
    # The registry knows Solartec, but not this website: a guessed URL is not identity.
    record = entity(_artifacts(tmp_path), legal_name="Solartec Energía SL", lei_value=SOLAR)
    loose = ControlledRegistry([record], loose=True)
    outcome = OrganizationAdmissionService(_store(tmp_path), loose).decide(
        "https://solartec-shop.example.com/"
    )
    assert outcome.status is AdmissionStatus.IDENTITY_PENDING
    assert outcome.reason_code == "SOURCE_RECORD_DOES_NOT_ATTEST_LOCATOR"
    assert _count(tmp_path) == 0


def test_a_near_name_match_from_a_search_source_is_never_admitted(tmp_path: Path) -> None:
    record = entity(_artifacts(tmp_path), legal_name="Solartec Energía Holding SL", lei_value=SOLAR)
    outcome = OrganizationAdmissionService(
        _store(tmp_path), ControlledRegistry([record], loose=True)
    ).decide("Solartec Energía")
    assert outcome.status is AdmissionStatus.IDENTITY_PENDING
    assert _count(tmp_path) == 0


def test_ambiguous_names_never_pick_a_winner(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    one = entity(
        artifacts, legal_name="Acme SL", lei_value=ACME_ONE, websites=("acme-one.example.com",)
    )
    two = entity(
        artifacts, legal_name="ACME  sl", lei_value=ACME_TWO, websites=("acme-two.example.com",)
    )
    registry = ControlledRegistry([one, two])
    service = OrganizationAdmissionService(_store(tmp_path), registry)
    # Source ambiguity: nothing is admitted.
    outcome = service.decide("Acme SL")
    assert (outcome.status, outcome.candidate_count) == (AdmissionStatus.AMBIGUOUS, 2)
    assert _count(tmp_path) == 0
    # Canonical ambiguity: both admitted by website; the bare name still decides nothing.
    assert service.decide("acme-one.example.com").status is AdmissionStatus.ADMITTED_NEW
    assert service.decide("acme-two.example.com").status is AdmissionStatus.ADMITTED_NEW
    canonical = service.decide("acme sl")
    assert (canonical.status, canonical.candidate_count) == (AdmissionStatus.AMBIGUOUS, 2)
    assert isinstance(service.resolve("acme sl"), OrganizationIdentityPending)
    # A verified key disambiguates.
    assert service.decide("Acme SL https://acme-two.example.com").organization.id == (  # type: ignore[union-attr]
        organization_id_for("LEI", "GLEIF", ACME_TWO)
    )


def test_signals_pointing_at_different_organizations_fail_closed(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    service = OrganizationAdmissionService(
        _store(tmp_path),
        ControlledRegistry(
            [
                entity(
                    artifacts,
                    legal_name="Acme SL",
                    lei_value=ACME_ONE,
                    websites=("acme-one.example.com",),
                ),
                entity(
                    artifacts,
                    legal_name="Beta SL",
                    lei_value=ACME_TWO,
                    websites=("beta.example.com",),
                ),
            ]
        ),
    )
    service.decide("acme-one.example.com")
    service.decide("beta.example.com")
    for locator in (
        "Acme SL https://beta.example.com/",
        f"LEI {ACME_ONE} https://beta.example.com/",
    ):
        outcome = service.decide(locator)
        assert outcome.status is AdmissionStatus.CONFLICT, locator
        assert isinstance(service.resolve(locator), OrganizationIdentityPending)
    assert _count(tmp_path) == 2


def test_a_key_held_by_another_identity_is_a_conflict_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    store = _store(tmp_path)
    OrganizationAdmissionService(
        store,
        ControlledRegistry(
            [
                entity(
                    artifacts,
                    legal_name="Acme SL",
                    lei_value=ACME_ONE,
                    websites=("shared.example.com",),
                )
            ]
        ),
    ).decide(f"LEI {ACME_ONE}")
    intruder = entity(
        artifacts, legal_name="Beta SL", lei_value=ACME_TWO, websites=("shared.example.com",)
    )
    outcome = OrganizationAdmissionService(store, ControlledRegistry([intruder])).decide(
        f"LEI {ACME_TWO}"
    )
    assert (outcome.status, outcome.reason_code) == (
        AdmissionStatus.CONFLICT,
        "WEBSITE_HELD_BY_ANOTHER_ORGANIZATION",
    )
    assert _count(tmp_path) == 1 and _count(tmp_path, "canonical_identifiers") == 1  # atomic


def test_admitted_identity_is_never_silently_replaced(tmp_path: Path) -> None:
    store = _store(tmp_path)
    OrganizationAdmissionService(store, ControlledRegistry([_solartec(tmp_path)])).decide(
        f"LEI {SOLAR}"
    )
    renamed = entity(
        _artifacts(tmp_path),
        legal_name="Solartec Energía SL",
        lei_value=SOLAR,
        record_name="Solartec Renamed SL",
        observed_at=datetime(2026, 10, 8, tzinfo=UTC),
    )
    with pytest.raises(IdentityConflictError) as exc:
        store.admit(*_admitted(renamed))
    assert exc.value.code == "ADMITTED_LEGAL_NAME_DIFFERS"
    organization = store.get_organization(organization_id_for("LEI", "GLEIF", SOLAR))
    assert organization is not None and organization.canonical_name == "Solartec Energía SL"


def test_replay_and_new_registry_observation_reuse_the_same_identity(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first = store.admit(*_admitted(_solartec(tmp_path)))
    again = store.admit(*_admitted(_solartec(tmp_path)))
    later = entity(
        _artifacts(tmp_path),
        legal_name="Solartec Energía SL",
        lei_value=SOLAR,
        websites=("https://www.solartec.example.com/",),
        observed_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    refreshed = store.admit(*_admitted(later))
    assert first == (organization_id_for("LEI", "GLEIF", SOLAR), True)
    assert again[1] is False and refreshed[1] is False
    assert _count(tmp_path) == 1


def test_concurrent_admissions_create_exactly_one_identity(tmp_path: Path) -> None:
    records = [_solartec(tmp_path) for _ in range(8)]
    results: list[tuple[OrganizationId, bool]] = []
    errors: list[BaseException] = []

    def admit(record: RegistryIdentityRecord) -> None:
        try:
            results.append(_store(tmp_path).admit(*_admitted(record)))
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=admit, args=(record,)) for record in records]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    assert len({organization for organization, _ in results}) == 1
    assert sum(created for _, created in results) == 1
    assert _count(tmp_path) == 1 and _count(tmp_path, "canonical_websites") == 1


def test_only_registry_evidence_admitted_by_evidence_admission_can_write(tmp_path: Path) -> None:
    store = _store(tmp_path)
    record = _solartec(tmp_path)
    # A non-registry source (e.g. the website itself, or a model) proposing identity.
    web = replace(record.legal_name.evidence, authority=SourceAuthority.OFFICIAL_WEB)
    proposed = RegistryIdentityRecord(
        replace(record.legal_name, evidence=web), record.registrations, record.official_websites
    )
    outcome = OrganizationAdmissionService(store, ControlledRegistry([proposed])).decide(
        f"LEI {SOLAR}"
    )
    assert (outcome.status, outcome.reason_code) == (
        AdmissionStatus.IDENTITY_PENDING,
        "IDENTITY_EVIDENCE_NOT_ADMITTED",
    )
    # Calling the store directly with a decision for different evidence is refused too.
    legal, registrations, websites = _admitted(record)
    forged = AdmittedProposition(proposed.legal_name, legal.decision)
    with pytest.raises((EvidenceAdmissionRequired, OrganizationMaterializationError)):
        store.admit(forged, registrations, websites)
    assert _count(tmp_path) == 0


def test_subject_must_be_derived_from_the_registry_identifier(tmp_path: Path) -> None:
    record = _solartec(tmp_path)
    moved = OrganizationId("org:registry:chosen-by-caller")

    def rebind(request):  # type: ignore[no-untyped-def]
        claim = replace(request.evidence.grounded_claim, subject_id=moved)
        evidence = replace(
            request.evidence,
            observation_subject_id=moved,
            grounded_claim=claim,
            representation=replace(request.evidence.representation, subject_id=moved),
        )
        return replace(request, evidence=evidence, subject_id=moved)

    hijacked = RegistryIdentityRecord(
        rebind(record.legal_name),
        tuple(rebind(item) for item in record.registrations),
        tuple(rebind(item) for item in record.official_websites),
    )
    outcome = OrganizationAdmissionService(_store(tmp_path), ControlledRegistry([hijacked])).decide(
        f"LEI {SOLAR}"
    )
    assert outcome.reason_code == "REGISTRY_RECORD_SUBJECT_MISMATCH"
    # The control plane will not bind or admit it either, so nothing can reach the store.
    assert prepare_admission(hijacked) is None
    assert _count(tmp_path) == 0


def test_integrity_loss_withholds_the_identity_instead_of_duplicating_it(tmp_path: Path) -> None:
    service = OrganizationAdmissionService(
        _store(tmp_path), ControlledRegistry([_solartec(tmp_path)])
    )
    assert service.decide(f"LEI {SOLAR}").status is AdmissionStatus.ADMITTED_NEW
    for artifact in (tmp_path / "artifacts").rglob("*"):
        if artifact.is_file():
            artifact.write_bytes(b"tampered")
    outcome = service.decide(f"LEI {SOLAR}")
    assert (outcome.status, outcome.reason_code) == (
        AdmissionStatus.IDENTITY_PENDING,
        "IDENTITY_REVALIDATION_REQUIRED",
    )
    assert _count(tmp_path) == 1


def test_internal_identifiers_never_reach_a_source_or_the_store(tmp_path: Path) -> None:
    registry = ControlledRegistry([_solartec(tmp_path)])
    service = OrganizationAdmissionService(_store(tmp_path), registry)
    service.decide(f"LEI {SOLAR}")
    calls = registry.calls
    organization_id = str(organization_id_for("LEI", "GLEIF", SOLAR))
    for locator in (organization_id, "focus_abc", "ops@solartec.example.com"):
        assert service.decide(locator).status is AdmissionStatus.INVALID_INPUT
        assert isinstance(service.resolve(locator), OrganizationIdentityRejected)
    assert registry.calls == calls


def test_resolve_returns_only_the_canonical_organization(tmp_path: Path) -> None:
    service = OrganizationAdmissionService(
        _store(tmp_path), ControlledRegistry([_solartec(tmp_path)])
    )
    resolved = service.resolve("Solartec Energía SL")
    assert isinstance(resolved, Organization)
    assert resolved == _store(tmp_path).get_organization(resolved.id)


def _admitted(record: RegistryIdentityRecord) -> PreparedAdmission:
    prepared = prepare_admission(record)
    assert prepared is not None
    return prepared


class _BrokenRegistry:
    calls = 0

    def lookup(self, locator):  # type: ignore[no-untyped-def]
        raise TimeoutError("registry did not answer")


def test_a_failing_source_is_unknown_not_an_error(tmp_path: Path) -> None:
    outcome = OrganizationAdmissionService(_store(tmp_path), _BrokenRegistry()).decide(
        "Solartec Energía SL"
    )
    assert (outcome.status, outcome.reason_code) == (
        AdmissionStatus.IDENTITY_PENDING,
        "IDENTITY_SOURCE_UNAVAILABLE",
    )
    assert _count(tmp_path) == 0


def test_store_refusal_on_missing_artifacts_writes_nothing(tmp_path: Path) -> None:
    record = _solartec(tmp_path)
    for artifact in (tmp_path / "artifacts").rglob("*"):
        if artifact.is_file():
            artifact.unlink()
    outcome = OrganizationAdmissionService(_store(tmp_path), ControlledRegistry([record])).decide(
        f"LEI {SOLAR}"
    )
    assert (outcome.status, outcome.reason_code) == (
        AdmissionStatus.IDENTITY_PENDING,
        "IDENTITY_ADMISSION_REFUSED",
    )
    assert _count(tmp_path) == 0
