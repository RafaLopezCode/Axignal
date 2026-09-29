"""AXIGNAL-shaped deterministic corpus benchmark for semantic retrieval.

This corpus models economic facets, locale and geography. It is deliberately
synthetic: it validates quantization loss and retrieval plumbing, not production
embedding quality or evidence relevance.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from turboquant import TurboQuantIndex

DIMENSION = 384
CANDIDATES_PER_ARCHETYPE = 48
K_VALUES = (10, 50, 100)
SEED = 20260930

ARCHETYPES: tuple[tuple[str, str, str, str], ...] = (
    ("cold_chain", "industrial_refrigeration", "food_logistics", "temperature_control"),
    ("industrial_pumps", "fluid_handling", "manufacturing", "maintenance"),
    ("pvc_windows", "fenestration", "construction", "energy_efficiency"),
    ("food_packaging", "packaging", "food_manufacturing", "traceability"),
    ("solar_installation", "photovoltaics", "construction", "energy"),
    ("water_treatment", "filtration", "utilities", "water"),
    ("machine_tools", "cnc", "manufacturing", "precision"),
    ("commercial_kitchens", "catering_equipment", "hospitality", "food_service"),
    ("warehouse_automation", "intralogistics", "logistics", "automation"),
    ("medical_devices", "regulated_manufacturing", "healthcare", "compliance"),
    ("agri_inputs", "crop_inputs", "agriculture", "soil"),
    ("fleet_maintenance", "vehicle_service", "transport", "maintenance"),
)
LOCALES = ("es", "en", "fr", "de", "it", "pt")
GEOGRAPHIES = ("ES", "GB", "FR", "DE", "IT", "PT")


@dataclass(frozen=True)
class Row:
    identifier: str
    archetype: str
    locale: str
    geography: str
    vector: np.ndarray


def _basis(token: str) -> np.ndarray:
    seed = int.from_bytes(token.encode("utf-8"), "little", signed=False) % (2**32)
    rng = np.random.default_rng(seed)
    value = rng.normal(size=DIMENSION).astype(np.float32)
    return value / np.linalg.norm(value)


def _vector(tokens: tuple[str, ...], noise_seed: int) -> np.ndarray:
    value = sum((_basis(token) for token in tokens), start=np.zeros(DIMENSION, dtype=np.float32))
    rng = np.random.default_rng(noise_seed)
    value += 0.08 * rng.normal(size=DIMENSION).astype(np.float32)
    return value / np.linalg.norm(value)


def build_corpus() -> tuple[list[Row], list[Row]]:
    candidates: list[Row] = []
    queries: list[Row] = []
    counter = 0
    for archetype, capability, market, theme in ARCHETYPES:
        for index in range(CANDIDATES_PER_ARCHETYPE):
            locale = LOCALES[index % len(LOCALES)]
            geography = GEOGRAPHIES[index % len(GEOGRAPHIES)]
            tokens = (archetype, capability, market, theme, f"locale:{locale}", f"geo:{geography}")
            candidates.append(
                Row(
                    f"org:{archetype}:{index:02d}",
                    archetype,
                    locale,
                    geography,
                    _vector(tokens, SEED + counter),
                )
            )
            counter += 1
        for locale, geography in zip(LOCALES, GEOGRAPHIES, strict=True):
            tokens = (archetype, capability, market, theme, f"locale:{locale}", f"geo:{geography}")
            queries.append(
                Row(
                    f"xeed:{archetype}:{locale}",
                    archetype,
                    locale,
                    geography,
                    _vector(tokens, SEED + 100_000 + counter),
                )
            )
            counter += 1
    return candidates, queries


def exact_search(matrix: np.ndarray, queries: np.ndarray, k: int) -> np.ndarray:
    return np.argsort(-(queries @ matrix.T), axis=1)[:, :k]


def recall_at(reference: np.ndarray, approximate: np.ndarray, k: int) -> float:
    return float(
        np.mean(
            [
                len(set(reference[i, :k]) & set(approximate[i, :k])) / k
                for i in range(reference.shape[0])
            ]
        )
    )


def germination_recall(rows: list[Row], queries: list[Row], result: np.ndarray, k: int) -> float:
    recalls: list[float] = []
    for query_index, query in enumerate(queries):
        gold = {
            index
            for index, row in enumerate(rows)
            if row.archetype == query.archetype
            and row.locale == query.locale
            and row.geography == query.geography
        }
        found = set(result[query_index, :k])
        recalls.append(len(gold & found) / len(gold))
    return float(np.mean(recalls))


def main() -> None:
    candidates, queries = build_corpus()
    matrix = np.stack([row.vector for row in candidates])
    query_matrix = np.stack([row.vector for row in queries])
    max_k = max(K_VALUES)
    exact = exact_search(matrix, query_matrix, max_k)
    report: dict[str, object] = {
        "schema_version": 1,
        "corpus": {
            "kind": "SYNTHETIC_AXIGNAL_SHAPED",
            "promotion_authority": False,
            "candidates": len(candidates),
            "queries": len(queries),
            "dimension": DIMENSION,
            "archetypes": len(ARCHETYPES),
            "locales": list(LOCALES),
            "geographies": list(GEOGRAPHIES),
            "warning": "Measures quantization loss only; not production embedding or evidence quality.",
        },
        "exact": {
            f"germination_recall@{k}": germination_recall(candidates, queries, exact, k)
            for k in K_VALUES
        },
        "turboquant": {},
    }
    variants: dict[str, object] = {}
    for bits in (8, 6, 4):
        start = time.perf_counter()
        index = TurboQuantIndex(
            dimension=DIMENSION,
            num_bits=bits,
            metric="cosine",
            use_qjl=True,
            seed=42,
            memory_efficient=True,
        )
        index.add(matrix)
        build_seconds = time.perf_counter() - start
        start = time.perf_counter()
        _, approximate = index.search(query_matrix, k=max_k)
        query_seconds = time.perf_counter() - start
        metrics: dict[str, float] = {
            "compression_ratio": float(index.compression_ratio),
            "build_seconds": build_seconds,
            "query_ms_each": 1000 * query_seconds / len(queries),
        }
        for k in K_VALUES:
            metrics[f"recall@{k}"] = recall_at(exact, approximate, k)
            metrics[f"germination_recall@{k}"] = germination_recall(
                candidates, queries, approximate, k
            )
        variants[str(bits)] = metrics
    report["turboquant"] = variants

    target = Path(__file__).with_name("results") / "axignal_corpus_latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
