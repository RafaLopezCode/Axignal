"""FR-17 Learning Events From Real Execution contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prime_execution_emits_separate_acquisition_and_ingestion_events() -> None:
    script = (ROOT / "application" / "economic_discovery" / "prime_execution.py").read_text(
        encoding="utf-8"
    )

    assert "LearningEventKind.SOURCE_ACQUISITION" in script
    assert "LearningEventKind.OBSERVATION_INGESTION" in script
    assert '"SOURCE_ACQUIRED"' in script
    assert '"OBSERVATION_INGESTED"' in script
    assert '"OBSERVATION_REPLAY_NO_CHANGE"' in script
    assert "observations_added=1 if source_result.mutation.inserted else 0" in script


def test_execution_event_ids_are_causally_orderable_within_one_run() -> None:
    script = (ROOT / "application" / "economic_discovery" / "prime_execution.py").read_text(
        encoding="utf-8"
    )
    runtime = (ROOT / "application" / "xeed_germination" / "runtime.py").read_text(encoding="utf-8")

    assert ":00-bootstrap:" in runtime
    assert ":01-source:" in script
    assert ":02-ingestion:" in script
    assert ":03-representation:" in script
    assert ":04-semantic:" in script
    assert ":05-prime:" in script
    assert "for item_index, item in enumerate(prime_plan.items)" in script


def test_bootstrap_reuse_is_derived_from_rich_state_not_caller_input() -> None:
    bootstrap = (ROOT / "application" / "xeed_germination" / "bootstrap.py").read_text(
        encoding="utf-8"
    )

    signature = bootstrap.split("def build_bootstrap_plan(", 1)[1].split(") -> BootstrapPlan:", 1)[
        0
    ]
    assert "reused_observation_count" not in signature
    assert "len({item.observation_id for item in rich_state.data})" in bootstrap


def test_runtime_bootstrap_application_must_emit_learning_memory_event() -> None:
    runtime = (ROOT / "application" / "xeed_germination" / "runtime.py").read_text(encoding="utf-8")

    signature = runtime.split("def apply_bootstrap_plan(", 1)[1].split(") -> None:", 1)[0]
    assert "learning_memory: LearningMemory" in signature
    assert "execution_id: str" in signature
    assert "code_sha: str" in signature
    assert "learning_memory.append(event)" in runtime
    assert "LearningYield(observations_reused=plan.reused_observation_count)" in runtime


def test_derived_yield_counts_come_from_observed_execution_state() -> None:
    script = (ROOT / "application" / "economic_discovery" / "prime_execution.py").read_text(
        encoding="utf-8"
    )

    assert "dimensions_became_answerable = len(answerable_after - answerable_before)" in script
    assert "semantic_judgments_produced=len(candidate_set.candidates)" in script
    assert "if item.route is PrimeRoute.ADAPTIVE_RESEARCH and result.made_progress" in script
    assert "research_objectives_resolved=result." not in script


def test_learning_store_persists_reuse_and_reads_legacy_payloads_as_zero_reuse() -> None:
    store = (ROOT / "pipeline" / "learning_memory" / "sqlite_store.py").read_text(encoding="utf-8")

    assert '"observations_reused": event.yield_.observations_reused' in store
    assert 'yield_data.get("observations_reused", 0)' in store
