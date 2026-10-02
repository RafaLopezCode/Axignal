"""Prepare a pinned Obscura release outside the repository."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CandidateAsset:
    filename: str
    sha256: str


ASSETS = {
    "windows-x86_64": CandidateAsset(
        "obscura-x86_64-windows.zip",
        "781a1b8bd12b65ec5aba95842e75e6f56b3101d360397506c0e35fe3f78536e8",
    ),
    "linux-x86_64": CandidateAsset(
        "obscura-x86_64-linux.tar.gz",
        "1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec",
    ),
}
BASE_URL = "https://github.com/h4ckf0r0day/obscura/releases/download/v0.2.3"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(ASSETS), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()

    asset = ASSETS[args.platform]
    args.root.mkdir(parents=True, exist_ok=True)
    archive = args.root / asset.filename

    if not archive.exists():
        if args.verify_existing:
            raise FileNotFoundError(archive)
        with (
            urllib.request.urlopen(f"{BASE_URL}/{asset.filename}") as response,
            archive.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)

    actual = digest(archive)
    if actual != asset.sha256:
        raise ValueError(f"checksum mismatch: {actual}")

    if args.verify_existing:
        print(f"VERIFIED {archive} {actual}")
        return 0

    destination = args.root / f"obscura-v0.2.3-{args.platform}"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(destination)
    else:
        with tarfile.open(archive, "r:gz") as bundle:
            bundle.extractall(destination, filter="data")
    print(f"PREPARED {destination} {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
