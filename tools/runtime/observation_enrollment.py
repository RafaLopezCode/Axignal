"""Server-owned reconcile/check/one-shot First Proof. No identity or market CLI inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from importlib import import_module
from pathlib import Path
from tempfile import NamedTemporaryFile

from application.economic_discovery.observation_memory import (
    GovernedObservation,
)
from application.observation_intelligence.loop import SourceObservationPort
from application.observation_runtime.materialization import (
    DesiredObservation,
    Readiness,
    derive_observation,
)
from application.subscriber_access.pilot import PilotAccessService
from application.subscriber_identity.runtime import Clock, SystemClock
from application.subscriber_portfolio.models import EntitlementSnapshot, PortfolioEntry
from application.subscriber_projection.evidence_delivery import content_reusable_history
from application.subscriber_projection.subscriber_runtime import _authorized_public_history
from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganizationReader,
    OrganizationReadError,
)
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    TrustedRequestContext,
    XeedReadError,
)
from domain.evidence.epistemics import Currentness
from domain.identity import PrincipalId, XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore
from tools.runtime.evidence_content import LiveEvidenceContentRights
from tools.runtime.first_observation import first_observation_reader, load_content_rights
from tools.runtime.observation_daily import (
    SUBSCRIBER_REUSE_POLICY,
    SUBSCRIBER_TEMPORAL_POLICY,
    load_enrollment,
    run_scheduled_tick,
)
from tools.runtime.subscriber_composition import _ProjectionEntitlements
from tools.runtime.subscriber_configuration import load_subscriber_settings
from tools.runtime.subscriber_observation import load_observation_attention
from tools.runtime.subscriber_provisioning import _ACCOUNT_REF, _ENVIRONMENT_REF

ENROLLMENT = "enrollment.json"
ATTENTION = "attention.json"
MANIFEST = "materialization.json"
MAX_BYTES = 65536


class SubscriberObservationAuthority:
    """Read-only existing authorities; never initialize stores, sessions or providers."""

    def __init__(self, root: Path, clock: Clock, configuration_file: Path | None = None):
        self.root, self.clock = root, clock
        self.identity = SqliteSubscriberIdentityStore(
            root / "subscriber-runtime.sqlite3", read_only=True
        )
        self.portfolio = SqliteSubscriberPortfolioStore(
            root / "subscriber-runtime.sqlite3", read_only=True
        )
        settings = load_subscriber_settings(os.environ, configuration_file=configuration_file)
        self.settings = settings
        self.enabled = settings.enabled
        self.pilot = (
            PilotAccessService(
                SqlitePilotAccessStore(root / "subscriber-pilot.sqlite3", read_only=True)
            )
            if settings.pilot_enabled and (root / "subscriber-pilot.sqlite3").is_file()
            else None
        )
        values = settings.values
        self.website_rights = load_content_rights(values)
        self.content_rights = LiveEvidenceContentRights(self.website_rights, clock.now)
        environment = (
            _ENVIRONMENT_REF
            if (
                values.get("AXIGNAL_STRIPE_LIVE_ENABLED") == "true"
                and values.get("AXIGNAL_STRIPE_ACCOUNT_ID") == _ACCOUNT_REF
            )
            else None
        )
        self.entitlements = _ProjectionEntitlements(
            SqliteSubscriberBillingStore(root / "subscriber-billing.sqlite3", read_only=True),
            clock,
            environment,
            self.pilot,
        )
        self.organizations = SqliteCanonicalOrganizationStore(
            root / "canonical-organizations.sqlite3",
            integrity=ContentAddressedArtifactIntegrityAdapter(
                ContentAddressedArtifactStore(root / "artifacts", read_only=True)
            ),
            governance=SqliteIdentityGovernanceStore(
                root / "identity-governance.sqlite3", read_only=True
            ),
            read_only=True,
        )
        self.authorized = AuthorizedXeedReader(self.identity, self.identity, self.portfolio)
        self.organization_reader = AuthorizedXeedOrganizationReader(self.organizations)
        self.memory = SqliteObservationMemory(root / "observation-memory.sqlite3", read_only=True)

    def contexts(self) -> tuple[TrustedRequestContext, ...]:
        if not self.enabled or not self.identity.path.is_file():
            return ()
        return tuple(
            TrustedRequestContext(c.principal_id, c.tenant_id)
            for c in self.identity.observation_contexts()
        )

    def entitlement(self, context: TrustedRequestContext) -> EntitlementSnapshot:
        # An absent Billing database cannot turn pilot-only readiness into a write.
        if not self.entitlements.billing_store.path.is_file():
            grant = (
                None
                if self.pilot is None
                else self.pilot.active_grant(context.tenant_id, now=self.clock.now())
            )
            return EntitlementSnapshot(
                None if grant is None else grant.capacity,
                Currentness.UNKNOWN if grant is None else Currentness.CURRENT,
                None if grant is None else grant.granted_at,
            )
        return self.entitlements.snapshot(context.tenant_id)

    def pilot_principal(self, context: TrustedRequestContext) -> PrincipalId | None:
        if self.pilot is None:
            return None
        grant = self.pilot.active_grant(context.tenant_id, now=self.clock.now())
        if grant is None:
            return None
        # Billing's verified entitlement has precedence in the existing policy.
        if (
            self.entitlements.billing_store.path.is_file()
            and self.entitlements.source(context.tenant_id) == "BILLING"
        ):
            return None
        return grant.principal_id

    def focuses(self, context: TrustedRequestContext) -> tuple[PortfolioEntry, ...]:
        return self.portfolio.list_authorized(context)

    def seed(
        self, context: TrustedRequestContext, focus: XeedId, now: datetime
    ) -> tuple[str, tuple[tuple[GovernedObservation, Currentness], ...]] | None:
        try:
            authorized = self.organization_reader.read(self.authorized.read(context, focus))
        except (XeedReadError, OrganizationReadError):
            return None
        if not self.memory._path.is_file():
            return str(authorized.organization.id), ()
        history = _authorized_public_history(
            memory=self.memory,
            organization_id=authorized.organization.id,
            xeed_id=focus,
            tenant_id=context.tenant_id,
            as_of=now,
            reuse_policy=SUBSCRIBER_REUSE_POLICY,
            temporal_policy=SUBSCRIBER_TEMPORAL_POLICY,
        )
        history = content_reusable_history(history, self.content_rights)
        return str(authorized.organization.id), history

    def first_observation(
        self, context: TrustedRequestContext, focus: XeedId
    ) -> Mapping[str, object] | None:
        """The Focus's stored First Proof (spec 063), read-only; None without a store."""
        reader = first_observation_reader(
            self.root, rights=self.website_rights, clock=self.clock.now
        )
        return None if reader is None else reader(context, focus)

    def allows(self, context: TrustedRequestContext, focus: XeedId, now: datetime) -> bool:
        """Fresh authorization and same deterministic capacity selection; no session."""
        desired = derive_observation(self, now=now)
        return any(e.context == context and e.focus_id == focus for e in desired.entries)


def snapshot_bytes(desired: DesiredObservation) -> dict[str, bytes]:
    enrollment = [
        {
            "tenantId": str(e.context.tenant_id),
            "principalId": str(e.context.principal_id),
            "focusId": str(e.focus_id),
        }
        for e in desired.entries
    ]
    by_org: dict[str, set[tuple[str, tuple[str, ...]]]] = {}
    for e in desired.entries:
        if e.markets:
            by_org.setdefault(e.organization_id, set()).update(
                (m.geography.code, tuple(sorted(r.value for r in m.roles))) for m in e.markets
            )
    attention = [
        {
            "organizationId": org,
            "markets": [
                {"jurisdiction": code, "roles": list(roles)} for code, roles in sorted(scopes)
            ],
        }
        for org, scopes in sorted(by_org.items())
    ]

    def encode(value: object) -> bytes:
        result = (
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        if len(result) > MAX_BYTES:
            raise ValueError("materialization size bound exceeded")
        return result

    result = {ENROLLMENT: encode(enrollment), ATTENTION: encode(attention)}
    result[MANIFEST] = encode(
        {
            "version": 1,
            "sha256": {name: hashlib.sha256(value).hexdigest() for name, value in result.items()},
        }
    )
    return result


def validate_manifest(manifest: Path, enrollment: Path, attention: Path) -> bool:
    try:
        if any(p.stat().st_size > MAX_BYTES for p in (manifest, enrollment, attention)):
            return False
        raw = json.loads(manifest.read_bytes())
        expected = {
            "version": 1,
            "sha256": {
                ENROLLMENT: hashlib.sha256(enrollment.read_bytes()).hexdigest(),
                ATTENTION: hashlib.sha256(attention.read_bytes()).hexdigest(),
            },
        }
        return bool(raw == expected)
    except (OSError, ValueError):
        return False


@contextmanager
def materialization_lock(root: Path, *, write: bool) -> Iterator[None]:
    path = root / ".reconcile.lock"
    if not write and not path.exists():
        yield
        return
    root.mkdir(parents=True, exist_ok=True) if write else None
    with path.open("a+b" if write else "rb") as handle:
        if write:
            os.chmod(path, 0o640)
            if os.name == "posix" and vars(os)["geteuid"]() == 0:
                vars(os)["chown"](path, 0, 33)
            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
        deadline = time.monotonic() + 10
        while True:
            try:
                if os.name == "posix":
                    fcntl = import_module("fcntl")

                    fcntl.flock(handle, fcntl.LOCK_NB | (fcntl.LOCK_EX if write else fcntl.LOCK_SH))
                else:
                    msvcrt = import_module("msvcrt")

                    handle.seek(0)
                    msvcrt.locking(
                        handle.fileno(), msvcrt.LK_NBLCK if write else msvcrt.LK_NBRLCK, 1
                    )
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("materialization lock unavailable") from None
                time.sleep(0.02)
        try:
            yield
        finally:
            if os.name == "posix":
                fcntl = import_module("fcntl")

                fcntl.flock(handle, fcntl.LOCK_UN)
            else:
                msvcrt = import_module("msvcrt")

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _current(root: Path, payloads: dict[str, bytes]) -> bool:
    try:
        if (
            os.name == "posix"
            and os.getenv("AXIGNAL_ENV") == "production"
            and any(
                (root / name).stat().st_uid != 0
                or (root / name).stat().st_gid != 33
                or (root / name).stat().st_mode & 0o777 != 0o640
                for name in payloads
            )
        ):
            return False
        return all(
            (root / name).is_file() and (root / name).read_bytes() == value
            for name, value in payloads.items()
        )
    except OSError:
        return False


def check(authority: SubscriberObservationAuthority, config_dir: Path) -> dict[str, object]:
    desired = derive_observation(authority, now=authority.clock.now())
    result = desired.summary()
    result["axent_available"] = bool(desired.entries) and (
        authority.settings.values.get("AXIGNAL_AXENT_GROUNDED", "false") == "true"
    )
    result["axent_provider_readiness"] = "NOT_CHECKED_NO_MODEL_DISPATCH"
    with materialization_lock(config_dir, write=False):
        current = _current(config_dir, snapshot_bytes(desired))
        any_files = any((config_dir / name).exists() for name in (ENROLLMENT, ATTENTION, MANIFEST))
        result["materialization_current"] = current
        if any_files and not current:
            result["state"] = Readiness.INVALID_MATERIALIZATION.value
        elif desired.entries and not current:
            result["state"] = "ENROLLMENT_NOT_MATERIALIZED"
    return result


def reconcile(authority: SubscriberObservationAuthority, config_dir: Path) -> dict[str, object]:
    desired = derive_observation(authority, now=authority.clock.now())
    if not desired.entries and not any(
        (config_dir / name).exists() for name in (ENROLLMENT, ATTENTION, MANIFEST)
    ):
        return dict(desired.summary(), changed=False)
    if (
        os.name == "posix"
        and os.getenv("AXIGNAL_ENV") == "production"
        and vars(os)["geteuid"]() != 0
    ):
        raise PermissionError("production reconciliation requires root operator")
    with materialization_lock(config_dir, write=True):
        # Re-derive under the lock: an older concurrent invocation cannot overwrite newer authority.
        desired = derive_observation(authority, now=authority.clock.now())
        payloads = snapshot_bytes(desired)
        if _current(config_dir, payloads):
            return dict(desired.summary(), changed=False)
        staged: dict[str, Path] = {}
        try:
            for name, payload in payloads.items():
                with NamedTemporaryFile(dir=config_dir, delete=False) as handle:
                    temp = Path(handle.name)
                    staged[name] = temp
                    os.chmod(temp, 0o640)
                    if os.name == "posix" and vars(os)["geteuid"]() == 0:
                        vars(os)["chown"](temp, 0, 33)
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            load_enrollment(staged[ENROLLMENT])
            load_observation_attention(staged[ATTENTION])
            if not validate_manifest(staged[MANIFEST], staged[ENROLLMENT], staged[ATTENTION]):
                raise ValueError("invalid staged generation")
            # Commit manifest last. A crash between replaces is detectable, never authorizes work.
            for name in (ENROLLMENT, ATTENTION, MANIFEST):
                os.replace(staged[name], config_dir / name)
            if os.name == "posix":
                descriptor = os.open(config_dir, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        finally:
            for temp in staged.values():
                temp.unlink(missing_ok=True)
        return dict(desired.summary(), changed=True)


def first_proof(
    authority: SubscriberObservationAuthority,
    config_dir: Path,
    *,
    code_sha: str,
    source_ports: Mapping[str, SourceObservationPort] | None = None,
) -> dict[str, object]:
    readiness = check(authority, config_dir)
    if readiness["state"] != Readiness.READY_FOR_MANUAL_TICK.value:
        return dict(readiness, manual_tick_status="NOT_EXECUTED")
    if source_ports is None:
        from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport

        source_ports = {
            "ted-search-v3": TedSearchAdapter(UrllibTedTransport(), clock=authority.clock.now)
        }
    summary = run_scheduled_tick(
        root=authority.root,
        clock=authority.clock,
        code_sha=code_sha,
        attention_file=config_dir / ATTENTION,
        enrollment=load_enrollment(config_dir / ENROLLMENT),
        source_ports=source_ports,
        research_access=authority.allows,
    )
    return dict(
        readiness,
        manual_tick_status=summary["state"],
        tick=summary,
        technical_execution=summary["state"] in {"COMPLETED", "ALREADY_COMPLETED"},
        economic_finding_produced=bool(summary.get("candidates_new")),
        work_count=summary.get("items", 0),
        evidence_count=summary.get("evidence_new", 0),
        brain_recomputed=summary.get("brain_recomputed", 0),
        model_calls=0,
        provider_calls=summary.get("requests", 0),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("reconcile", "check", "first-proof"))
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--configuration-file", type=Path)
    args = parser.parse_args(argv)
    try:
        authority = SubscriberObservationAuthority(
            args.data_dir.resolve(), SystemClock(), args.configuration_file
        )
        if args.operation == "reconcile":
            result = reconcile(authority, args.config_dir.resolve())
        elif args.operation == "check":
            result = check(authority, args.config_dir.resolve())
        else:
            result = first_proof(
                authority,
                args.config_dir.resolve(),
                code_sha=os.getenv("AXIGNAL_CODE_SHA", "UNKNOWN"),
            )
    except Exception as error:
        result = {
            "state": "AUTHORITY_OR_CONFIGURATION_UNAVAILABLE",
            "error_class": type(error).__name__,
            "model_calls": 0,
            "provider_calls": 0,
        }
    print(json.dumps(result))
    if result["state"] in {
        "AUTHORITY_OR_CONFIGURATION_UNAVAILABLE",
        Readiness.INVALID_MATERIALIZATION.value,
    }:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
