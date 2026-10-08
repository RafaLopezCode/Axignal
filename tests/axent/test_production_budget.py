"""T11 config, secret-file SDK options, hard budgets and restart-safe call audit."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from application.axent.grounded.answer import ANSWER_SCHEMA, ReasoningRequest, ReasoningResult
from application.axent.grounded.cost import CostRates
from application.axent.grounded.model_budget import BudgetedReasoner
from cognition.providers import luna_responses
from pipeline.axent.model_audit import SqliteModelAudit
from tests.axent.fixtures import NOW, ScriptedLuna
from tools.runtime.subscriber_axent import luna_reasoner_from_env


def request():
    return ReasoningRequest(
        "request:hash", "system", "user", ANSWER_SCHEMA, 500, "tenant:hash", "focus:hash"
    )


def budgeted(tmp_path, *, inner=None, tenant_calls=50):
    return BudgetedReasoner(
        inner or ScriptedLuna(),
        SqliteModelAudit(tmp_path / "audit.sqlite3", max_tenant_calls=tenant_calls),
        lambda: NOW,
        CostRates(Decimal(".1"), Decimal(".5"), "USD"),
        Decimal(".002"),
        "luna-responses",
    )


def test_budget_audit_has_usage_but_no_private_prompt(tmp_path: Path):
    bound = budgeted(tmp_path)
    result = bound.reason(request())
    assert result.audit_ref and result.model_calls == 1
    bound.audit.verified(result.audit_ref, route="ABSTAINED", dropped=0)
    with sqlite3.connect(tmp_path / "audit.sqlite3") as db:
        row = db.execute(
            "SELECT purpose, provider, model, cost, verification FROM axent_model_calls"
        ).fetchone()
        assert row == ("GROUNDED_ANSWER", "luna-responses", "gpt-6-luna", "0.0000302", "ABSTAINED")
        assert not any(
            "prompt" in r[1] or "credential" in r[1]
            for r in db.execute("PRAGMA table_info(axent_model_calls)")
        )


def test_durable_quota_has_one_authority_under_concurrency(tmp_path: Path):
    bound = budgeted(tmp_path, tenant_calls=2)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: bound.reason(request()), range(4)))
    assert sum(r.model_calls for r in results) == 2
    assert sum(r.error_class == "RATE_LIMITED" for r in results) == 2
    restarted = budgeted(tmp_path, tenant_calls=2)
    assert restarted.reason(request()).model_calls == 0


@pytest.mark.parametrize(
    "change", [{"user": "x" * 8001}, {"max_output_tokens": 501}, {"tenant_ref": ""}]
)
def test_preflight_denial_means_zero_provider_calls(tmp_path: Path, change):
    luna = ScriptedLuna()
    result = budgeted(tmp_path, inner=luna).reason(replace(request(), **change))
    assert result.model_calls == 0 and result.error_class == "BUDGET_BLOCKED" and not luna.requests


def test_unknown_usage_is_unavailable_and_never_an_answer(tmp_path: Path):
    class Unknown:
        model = "gpt-6-luna"

        def reason(self, request):
            return ReasoningResult(
                {"claims": [{"text": "invented", "refs": ["E1"]}]}, self.model, None, None, 1
            )

    result = budgeted(tmp_path, inner=Unknown()).reason(request())
    assert not result.payload and result.error_class == "USAGE_UNKNOWN"


def config(tmp_path):
    key = tmp_path / "key"
    key.write_text("fake-test-credential", encoding="utf-8")
    return {
        "AXIGNAL_AXENT_GROUNDED": "true",
        "AXIGNAL_AXENT_LUNA_MODEL": "gpt-6-luna",
        "AXIGNAL_AXENT_API_KEY_FILE": str(key),
        "AXIGNAL_AXENT_INPUT_PER_MILLION": ".1",
        "AXIGNAL_AXENT_OUTPUT_PER_MILLION": ".5",
        "AXIGNAL_AXENT_MAX_CALL_COST": ".002",
    }


@pytest.mark.parametrize("value", ["", "0", "NaN", "Infinity", "-1"])
def test_unknown_or_invalid_cost_config_disables_provider(tmp_path: Path, value):
    values = config(tmp_path)
    values["AXIGNAL_AXENT_INPUT_PER_MILLION"] = value
    assert luna_reasoner_from_env(values, data_dir=tmp_path) is None


def test_flag_missing_key_and_enabled_composition(tmp_path: Path):
    values = config(tmp_path)
    assert isinstance(luna_reasoner_from_env(values, data_dir=tmp_path), BudgetedReasoner)
    values["AXIGNAL_AXENT_GROUNDED"] = "false"
    assert luna_reasoner_from_env(values, data_dir=tmp_path) is None
    values["AXIGNAL_AXENT_GROUNDED"] = "true"
    values["AXIGNAL_AXENT_API_KEY_FILE"] = str(tmp_path / "missing")
    assert luna_reasoner_from_env(values, data_dir=tmp_path) is None


def test_sdk_secret_file_has_timeout_no_retries_and_no_env_copy(tmp_path: Path, monkeypatch):
    key = tmp_path / "key"
    key.write_text("fake-test-credential", encoding="utf-8")
    options = {}

    def factory(**kwargs):
        options.update(kwargs)
        return SimpleNamespace(responses=object())

    monkeypatch.setattr(luna_responses, "import_module", lambda _: SimpleNamespace(OpenAI=factory))
    luna_responses._default_sdk(key)
    assert options["api_key"] == "fake-test-credential"
    assert options["max_retries"] == 0 and options["timeout"] == 15.0


def test_live_probe_same_contract_offline_and_replay_guard(tmp_path: Path, monkeypatch):
    from tools.runtime import axent_preflight

    root = tmp_path / "isolated"
    scripted = ScriptedLuna(
        script=lambda _: {
            "claims": [],
            "unknowns": ["award unknown"],
            "insufficient_evidence": True,
        }
    )

    def factory(values, *, data_dir):
        return BudgetedReasoner(
            scripted,
            SqliteModelAudit(data_dir / "axent-model-audit.sqlite3"),
            lambda: NOW,
            CostRates(Decimal(".1"), Decimal(".5"), "USD"),
            Decimal(".002"),
            "luna-responses",
        )

    monkeypatch.setattr(axent_preflight, "luna_reasoner_from_env", factory)
    configuration = (
        Path(__file__).resolve().parents[2] / "deploy/production/subscriber-runtime.example.conf"
    )
    result = axent_preflight.run(root, configuration, tmp_path / "fake-key")
    assert result["state"] == "PASS" and result["model_calls"] == result["research_requests"] == 1
    assert result["canonical_writes"] == result["source_http_calls"] == 0
    assert result["controlled_observations"] == 1
    with pytest.raises(RuntimeError, match="already attempted"):
        axent_preflight.run(root, configuration, tmp_path / "fake-key")
    assert len(scripted.requests) == 1
