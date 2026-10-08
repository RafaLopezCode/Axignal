"""Spec 062 / ADR-0090: the semantic layer is deployable, off by default and bounded.

These checks guard the production path, not only the code: the TypeSafe key reaches
the runtime alone, the SDK is in the runtime image without a second pin, disabled
composition touches neither SDK nor credential, and Jev judgments have no consumer
that could turn them into training data.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "deploy" / "production"


def _services_block(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            current = line.strip()[:-1]
            blocks[current] = ""
        elif line and not line.startswith(" "):
            current = None
        elif current is not None:
            blocks[current] += line + "\n"
    return blocks


def test_typesafe_key_is_mounted_into_the_runtime_only() -> None:
    text = (PRODUCTION / "compose.semantic.override.yml").read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    overlay = "\n".join(lines)
    services = _services_block(overlay.split("\nsecrets:")[0])
    assert set(services) == {"runtime"}
    assert "- typesafe_api_key" in services["runtime"]
    assert "AXIGNAL_SEMANTIC_LAYER_ENABLED" not in overlay  # mounting never activates
    assert (
        "file: ${AXIGNAL_TYPESAFE_API_KEY_HOST_FILE:-/etc/axignal/secrets/typesafe_api_key}"
        in overlay
    )
    assert "environment:" not in overlay  # never a key in environment variables
    for other in ("compose.yml", "compose.subscriber.override.yml", "compose.axent.override.yml"):
        # The mandatory compositions do not require the host file to exist.
        assert "typesafe" not in (PRODUCTION / other).read_text(encoding="utf-8").lower()


def test_runtime_image_installs_the_pinned_sdk_once_and_no_secret() -> None:
    dockerfile = (PRODUCTION / "docker" / "subscriber-runtime.Dockerfile").read_text(
        encoding="utf-8"
    )
    assert "--group semantic-layer-live" in dockerfile
    assert "secret" not in dockerfile.lower().replace("no credential", "")
    assert "TYPESAFE" not in dockerfile
    groups = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "dependency-groups"
    ]
    assert groups["semantic-layer-live"] == ["typesafe-sdk==0.7.1"]
    assert groups["decision-lab-live"] == [{"include-group": "semantic-layer-live"}]
    for experience_like in ("experience.Dockerfile", "landing.Dockerfile"):
        assert "semantic-layer-live" not in (PRODUCTION / "docker" / experience_like).read_text(
            encoding="utf-8"
        )


def test_production_example_keeps_the_layer_off() -> None:
    conf = (PRODUCTION / "subscriber-runtime.example.conf").read_text(encoding="utf-8")
    assert "AXIGNAL_SEMANTIC_LAYER_ENABLED=false" in conf
    assert "AXIGNAL_SEMANTIC_REASONING_CALLS=0" in conf
    assert "AXIGNAL_TYPESAFE_API_KEY_FILE=/run/secrets/typesafe_api_key" in conf


def _probe(code: str) -> str:
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_disabled_composition_imports_no_sdk_and_reads_no_credential(tmp_path: Path) -> None:
    out = _probe(
        "import sys, pathlib\n"
        "from tools.runtime.semantic_layer import semantic_screen_from_env\n"
        f"d = pathlib.Path({str(tmp_path)!r})\n"
        "print(semantic_screen_from_env({'AXIGNAL_SEMANTIC_LAYER_ENABLED': 'false',"
        " 'AXIGNAL_TYPESAFE_API_KEY_FILE': '/run/secrets/typesafe_api_key'}, data_dir=d))\n"
        "print('typesafe_sdk' in sys.modules, 'cognition.providers.typesafe_system_one' in sys.modules)\n"
        "print(sorted(p.name for p in d.iterdir()))\n"
    )
    assert out.splitlines() == ["None", "False False", "[]"]


def test_enabled_composition_defers_sdk_and_key_until_the_first_judgment(tmp_path: Path) -> None:
    key = tmp_path / "typesafe_api_key"
    key.write_text("placeholder-not-a-key", encoding="utf-8")
    out = _probe(
        "import sys, pathlib\n"
        "from tools.runtime.semantic_layer import semantic_screen_from_env\n"
        f"d = pathlib.Path({str(tmp_path)!r})\n"
        f"values = {{'AXIGNAL_SEMANTIC_LAYER_ENABLED': 'true', 'AXIGNAL_TYPESAFE_API_KEY_FILE': {str(key.resolve())!r}}}\n"
        "screen = semantic_screen_from_env(values, data_dir=d)\n"
        "print(type(screen).__name__ if screen else None)\n"
        "print('typesafe_sdk' in sys.modules)\n"
    )
    # Composed and wired, yet the SDK is still not imported and the key not read.
    assert out.splitlines() == ["SemanticDemandScreen", "False"]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_jev_judgments_have_no_training_or_export_consumer() -> None:
    # MCA §2.3(b) / ADR-0090: Jev outputs never become training or calibration data.
    # Judgment memory is readable only by the cascade's composition and its tests.
    allowed = {
        Path("tools/runtime/semantic_layer.py"),
        Path("tests/semantic_layer/test_providers.py"),
    }
    consumers = {
        path.relative_to(ROOT)
        for folder in (
            "application",
            "cognition",
            "domain",
            "pipeline",
            "tools",
            "experiments",
            "tests",
        )
        for path in (ROOT / folder).rglob("*.py")
        if "pipeline.semantic_layer.sqlite_memory" in _imports(path)
    }
    assert consumers <= allowed
    lab = ROOT / "experiments"
    assert not any(
        "application.semantic_layer" in _imports(path)
        or "cognition.providers.typesafe_system_one" in _imports(path)
        for path in lab.rglob("*.py")
    )


def test_the_contractual_decision_and_its_invariants_stay_on_record() -> None:
    adr = (ROOT / "docs/adr/ADR-0090-semantic-judgment-layer.md").read_text(encoding="utf-8")
    assert "**Status:** Accepted (CTO decision)" in adr
    assert "not a representation that TypeSafe supplied an amendment" in adr
    assert "Separate Agreement or an Order" in adr
    for forbidden in (
        "distillation",
        "imitation",
        "fine-tuning",
        "replacement evaluator",
        "resold",
    ):
        assert forbidden in adr
    eb05 = (ROOT / "docs/research/jev/EB05_JEV_ELIGIBILITY_REASSESSMENT_2026-10-05.md").read_text(
        encoding="utf-8"
    )
    assert "SUPERSEDED BY ADR-0090" in eb05
    assert "stricter internal fail-closed interpretation" in eb05
    assert "MODEL_PROVIDER_TRANSMISSION_ALLOWED=UNKNOWN" in eb05  # history is kept, not rewritten
