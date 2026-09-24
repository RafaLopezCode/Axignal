"""Canonical organizations.

One canonical Organization regardless of how many users Xignal it. Organization
identity is NOT scoped to a subscriber, account, tenant or Xignal.

Doctrine: MASTER §6.1, §7.3, §36 (Organization), §46.13.
"""

from __future__ import annotations

from domain.organizations.model import Organization, OrganizationError

__all__ = ["Organization", "OrganizationError"]
