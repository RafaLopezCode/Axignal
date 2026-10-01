"""Persistence adapters for Admin access authority."""

from pipeline.admin_access.sqlite_store import SqliteAdminAccessStore

__all__ = ["SqliteAdminAccessStore"]
