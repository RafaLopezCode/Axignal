"""A controlled, offline registry for spec 052 tests.

It implements the production ``RegistryIdentitySource`` port and builds its records
with the production ``registry_record`` builder over a real content-addressed artifact
store, so admission goes through EvidenceAdmission and the canonical store exactly as
it would with a real registry. The fictitious entities use RFC 2606 example domains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from application.organization_admission.locator import AttentionLocator, public_domain
from application.organization_admission.registry_record import (
    RegistryAttestation,
    registry_record,
)
from application.organization_admission.service import (
    RegistryIdentityRecord,
    RegistryLookup,
    RegistryLookupStatus,
    parse_registration,
)
from domain.identity import identity_name_key
from pipeline.source_acquisition import ContentAddressedArtifactStore

OBSERVED = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)


def lei(base: str) -> str:
    """A checksum-valid ISO 17442 LEI for an 18-character base (test identities only)."""
    base = base.upper()
    assert len(base) == 18
    digits = "".join(str(int(char, 36)) for char in base + "00")
    return f"{base}{98 - int(digits) % 97:02d}"


def entity(
    artifacts: ContentAddressedArtifactStore,
    *,
    legal_name: str,
    lei_value: str,
    websites: tuple[str, ...] = (),
    observed_at: datetime = OBSERVED,
    record_name: str | None = None,
) -> RegistryIdentityRecord:
    """One registry entry; ``record_name`` lets a test make the registry disagree."""

    name = record_name or legal_name
    lines = [
        f"Entry {lei_value} legal name: {name}",
        f"Registered as LEI {lei_value}",
        *(f"Entry {lei_value} registered website: {site}" for site in websites),
    ]
    attestations = [
        RegistryAttestation("legal_identity", name, lines[0], lei_value, "legal name", name),
        RegistryAttestation(
            "registration",
            f"LEI|GLEIF|{lei_value}",
            lines[1],
            lei_value,
            "Registered as",
            lei_value,
        ),
        *(
            RegistryAttestation(
                "official_website", site, line, lei_value, "registered website", site
            )
            for site, line in zip(websites, lines[2:], strict=True)
        ),
    ]
    return registry_record(
        document="\n".join(lines),
        source_ref=f"https://registry.example.com/lei/{lei_value}",
        observed_at=observed_at,
        artifacts=artifacts,
        identifier=("LEI", "GLEIF", lei_value),
        attestations=attestations,
    )


@dataclass
class ControlledRegistry:
    """Exact lookups by default; ``loose`` simulates a search API returning near matches."""

    records: list[RegistryIdentityRecord] = field(default_factory=list)
    available: bool = True
    loose: bool = False
    calls: int = 0

    def lookup(self, locator: AttentionLocator) -> RegistryLookup:
        self.calls += 1
        if not self.available:
            return RegistryLookup(RegistryLookupStatus.UNAVAILABLE)
        found = [record for record in self.records if self._matches(record, locator)]
        return RegistryLookup(
            RegistryLookupStatus.FOUND if found else RegistryLookupStatus.NOT_FOUND,
            tuple(found),
        )

    def _matches(self, record: RegistryIdentityRecord, locator: AttentionLocator) -> bool:
        if locator.identifier is not None:
            return any(
                parse_registration(item.object_or_value)[2] == locator.identifier.value
                for item in record.registrations
            )
        if locator.domain is not None:
            if self.loose:
                return True
            return any(
                public_domain(item.object_or_value) == locator.domain
                for item in record.official_websites
            )
        name = identity_name_key(record.legal_name.object_or_value)
        wanted = locator.name_key or ""
        return wanted in name if self.loose else name == wanted
