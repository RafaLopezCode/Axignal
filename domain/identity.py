"""Distinct static identity types using AXIGNAL's string ID representation."""

from __future__ import annotations

from typing import NewType

OrganizationId = NewType("OrganizationId", str)
PrincipalId = NewType("PrincipalId", str)
TenantId = NewType("TenantId", str)
XeedId = NewType("XeedId", str)
