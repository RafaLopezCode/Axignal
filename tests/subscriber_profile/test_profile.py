import base64
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from application.subscriber_profile.service import ProfileConflict, SubscriberProfileService
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import PrincipalId, TenantId
from pipeline.subscriber_profile.images import RasterAvatarNormalizer
from pipeline.subscriber_profile.store import SqliteProfileStore

A = TrustedRequestContext(PrincipalId("alice"), TenantId("tenant-a"))
B = TrustedRequestContext(PrincipalId("bob"), TenantId("tenant-b"))


def service(path: Path) -> SubscriberProfileService:
    return SubscriberProfileService(SqliteProfileStore(path), RasterAvatarNormalizer())


def png(size: tuple[int, int] = (200, 200), *, metadata: bool = False) -> bytes:
    image = Image.new("RGB", size, "blue")
    out = BytesIO()
    info = PngImagePlugin.PngInfo()
    if metadata:
        info.add_text("private", "sensitive EXIF-like comment")
    image.save(out, format="PNG", pnginfo=info)
    return out.getvalue()


def test_profile_ownership_durability_conflict_and_independent_fields(tmp_path: Path) -> None:
    path = tmp_path / "profile.sqlite3"
    s = service(path)
    assert s.read(A)["version"] == 0 and s.read(B)["locale"] is None
    changed = s.change(A, {"action": "locale", "version": 0, "locale": "fr"})
    assert changed["version"] == 1 and changed["locale"] == "fr"
    assert service(path).read(A) == changed and s.read(B)["locale"] is None
    with pytest.raises(ProfileConflict):
        s.change(A, {"action": "locale", "version": 0, "locale": "de"})
    avatar = s.change(
        A,
        {"action": "avatar", "version": 1, "image": base64.b64encode(png(metadata=True)).decode()},
    )
    assert avatar["locale"] == "fr" and avatar["version"] == 2
    raw = base64.b64decode(str(avatar["avatar"]).split(",")[1])
    image = Image.open(BytesIO(raw))
    assert image.size == (128, 128) and "private" not in image.info
    removed = s.change(A, {"action": "remove_avatar", "version": 2})
    assert removed["avatar"] is None and removed["locale"] == "fr"
    cleared = s.change(A, {"action": "locale", "locale": None, "version": 3})
    assert cleared["locale"] is None and cleared["avatar"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "locale", "version": True, "locale": "es"},
        {"action": "locale", "version": 0, "locale": "xx"},
        {"action": "locale", "version": 0, "locale": "es", "principalId": "bob"},
        {"action": "avatar", "version": 0, "image": "<svg/>"},
        {
            "action": "avatar",
            "version": 0,
            "image": base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>').decode(),
        },
        {"action": "avatar", "version": 0, "image": base64.b64encode(b"x" * 131073).decode()},
        {"action": "avatar", "version": 0, "image": base64.b64encode(png((2049, 1))).decode()},
        {"action": "remove_avatar", "version": 0, "tenantId": "tenant-b"},
    ],
)
def test_rejected_changes_do_not_save_or_advance_version(
    tmp_path: Path, payload: dict[str, object]
) -> None:
    s = service(tmp_path / "profile.sqlite3")
    with pytest.raises(ValueError):
        s.change(A, payload)
    assert s.read(A)["version"] == 0 and s.read(B)["version"] == 0


def test_principal_preference_is_the_same_across_its_tenant_contexts(tmp_path: Path) -> None:
    s = service(tmp_path / "profile.sqlite3")
    s.change(A, {"action": "locale", "version": 0, "locale": "it"})
    another = TrustedRequestContext(A.principal_id, TenantId("another-authorized-tenant"))
    assert s.read(another)["locale"] == "it"


def test_connections_close_on_success_and_conflict(tmp_path: Path, monkeypatch) -> None:
    import sqlite3

    import pipeline.subscriber_profile.store as module

    connections = []
    connect = sqlite3.connect

    def tracked(*args, **kwargs):
        db = connect(*args, **kwargs)
        connections.append(db)
        return db

    monkeypatch.setattr(module.sqlite3, "connect", tracked)
    s = service(tmp_path / "profile.sqlite3")
    s.read(A)
    s.change(A, {"action": "locale", "version": 0, "locale": "es"})
    with pytest.raises(ProfileConflict):
        s.change(A, {"action": "locale", "version": 0, "locale": "de"})
    for db in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            db.execute("SELECT 1")
