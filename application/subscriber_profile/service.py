"""Versioned private profile commands after subscriber authentication."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Protocol

from application.xeed_access.reader import TrustedRequestContext
from domain.identity import PrincipalId

LOCALES = frozenset({"es", "en", "de", "pt", "fr", "it"})
MAX_AVATAR_BYTES = 131072


class ProfileConflict(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    version: int = 0
    locale: str | None = None
    avatar: bytes | None = None

    def wire(self) -> dict[str, object]:
        return {
            "state": "success",
            "version": self.version,
            "locale": self.locale,
            "avatar": None
            if self.avatar is None
            else "data:image/png;base64," + base64.b64encode(self.avatar).decode("ascii"),
        }


class ProfileStore(Protocol):
    def read(self, principal: PrincipalId) -> Profile: ...
    def write(
        self,
        principal: PrincipalId,
        expected: int,
        *,
        locale: str | None = None,
        avatar: bytes | None = None,
        field: str,
    ) -> Profile: ...


class AvatarNormalizer(Protocol):
    def normalize(self, raw: bytes) -> bytes: ...


@dataclass
class SubscriberProfileService:
    store: ProfileStore
    images: AvatarNormalizer

    def read(self, context: TrustedRequestContext) -> dict[str, object]:
        return self.store.read(context.principal_id).wire()

    def change(
        self, context: TrustedRequestContext, payload: dict[str, object]
    ) -> dict[str, object]:
        action, version = payload.get("action"), payload.get("version")
        if type(version) is not int or version < 0:
            raise ValueError("invalid profile version")
        if action == "locale" and set(payload) == {"action", "version", "locale"}:
            locale = payload["locale"]
            if locale is not None and (not isinstance(locale, str) or locale not in LOCALES):
                raise ValueError("invalid locale")
            return self.store.write(
                context.principal_id, version, locale=locale, field="locale"
            ).wire()
        if action == "remove_avatar" and set(payload) == {"action", "version"}:
            return self.store.write(context.principal_id, version, field="avatar").wire()
        if action == "avatar" and set(payload) == {"action", "version", "image"}:
            encoded = payload["image"]
            if not isinstance(encoded, str) or len(encoded) > 174764:
                raise ValueError("avatar exceeds limit")
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error):
                raise ValueError("invalid avatar encoding") from None
            if not raw or len(raw) > MAX_AVATAR_BYTES:
                raise ValueError("avatar exceeds limit")
            image = self.images.normalize(raw)
            return self.store.write(
                context.principal_id, version, avatar=image, field="avatar"
            ).wire()
        raise ValueError("invalid profile command")
