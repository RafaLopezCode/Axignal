"""Admin shell navigation projection over AO-01 authorization grants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from domain.admin_access import AdminAuthorizationGrant, AdminScope


@dataclass(frozen=True, slots=True)
class AdminNavItem:
    slug: str
    label: str
    eyebrow: str
    description: str
    required_any: frozenset[AdminScope]


@dataclass(frozen=True, slots=True)
class AdminShellProjection:
    mode: str
    principal_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    current_slug: str
    navigation: tuple[AdminNavItem, ...]


ADMIN_NAV_ITEMS: Final[tuple[AdminNavItem, ...]] = (
    AdminNavItem(
        "command-center",
        "Command Center",
        "Executive state",
        "Operating state of AXIGNAL. Internal operational projection, not AXIGLAND truth.",
        frozenset({AdminScope.EXECUTIVE_READ}),
    ),
    AdminNavItem(
        "customers-crm",
        "Customers / CRM",
        "First-party operations",
        "AXIGNAL customer and internal commercial state only.",
        frozenset({AdminScope.CUSTOMERS_READ, AdminScope.COMMERCIAL_READ}),
    ),
    AdminNavItem(
        "acquisition",
        "Acquisition",
        "Growth operations",
        "Campaign, consent and acquisition state owned by AXIGNAL.",
        frozenset({AdminScope.ACQUISITION_READ}),
    ),
    AdminNavItem(
        "revenue",
        "Revenue",
        "Commercial economics",
        "Billing and revenue operations. Commercial outcome is not epistemic validity.",
        frozenset({AdminScope.REVENUE_READ, AdminScope.BILLING_READ}),
    ),
    AdminNavItem(
        "xeeds",
        "Xeeds",
        "Subscriber runtime",
        "Operational Xeed state and economics without changing AXIGLAND authority.",
        frozenset({AdminScope.XEEDS_READ}),
    ),
    AdminNavItem(
        "axigland-quality",
        "AXIGLAND Quality",
        "Economic memory quality",
        "Governed quality and currentness projection over canonical economic memory.",
        frozenset({AdminScope.QUALITY_READ}),
    ),
    AdminNavItem(
        "axent-brain",
        "AXENT / Brain",
        "Cognitive operations",
        "Research, providers and governed cognitive spend.",
        frozenset({AdminScope.RESEARCH_READ}),
    ),
    AdminNavItem(
        "governance",
        "Governance",
        "Policies & audit",
        "Versioned policy, audit and governance state.",
        frozenset({AdminScope.GOVERNANCE_READ, AdminScope.AUDIT_READ}),
    ),
    AdminNavItem(
        "integrations",
        "Integrations",
        "External capabilities",
        "Connection health and governed external-service operations.",
        frozenset({AdminScope.INTEGRATIONS_READ}),
    ),
    AdminNavItem(
        "finance-fiscal",
        "Finance / Fiscal",
        "Private financial operations",
        "Accounting and fiscal operations. Private state never becomes AXIGLAND truth.",
        frozenset({AdminScope.FINANCE_READ, AdminScope.FISCAL_READ}),
    ),
    AdminNavItem(
        "frontier-advisor",
        "Frontier Advisor",
        "Premium intelligence",
        "Staff-only advisory workbench over governed evidence.",
        frozenset({AdminScope.ADVISORY_READ}),
    ),
    AdminNavItem(
        "system",
        "System",
        "Runtime & incidents",
        "Runtime, infrastructure and incident state.",
        frozenset({AdminScope.SYSTEM_READ}),
    ),
)


class AdminShellRouteDenied(PermissionError):
    """Requested Admin domain is known but outside the current grant."""


class AdminShellRouteUnknown(LookupError):
    """Requested Admin domain does not exist."""


def _has_any(grant: AdminAuthorizationGrant, required: frozenset[AdminScope]) -> bool:
    return not required or not grant.scopes.isdisjoint(required)


def accessible_navigation(grant: AdminAuthorizationGrant) -> tuple[AdminNavItem, ...]:
    return tuple(item for item in ADMIN_NAV_ITEMS if _has_any(grant, item.required_any))


def project_admin_shell(
    grant: AdminAuthorizationGrant,
    *,
    requested_slug: str | None = None,
) -> AdminShellProjection:
    navigation = accessible_navigation(grant)
    if not navigation:
        raise AdminShellRouteDenied("Admin principal has no shell-visible scope")
    if requested_slug is None or requested_slug == "":
        current = navigation[0]
    else:
        known = next((item for item in ADMIN_NAV_ITEMS if item.slug == requested_slug), None)
        if known is None:
            raise AdminShellRouteUnknown(requested_slug)
        if not _has_any(grant, known.required_any):
            raise AdminShellRouteDenied(requested_slug)
        current = known
    return AdminShellProjection(
        mode="ADMIN",
        principal_id=str(grant.principal_id),
        roles=tuple(sorted(role.value for role in grant.roles)),
        scopes=tuple(sorted(scope.value for scope in grant.scopes)),
        current_slug=current.slug,
        navigation=navigation,
    )
