"""Deterministic synthetic smoke benchmark; never a promotion corpus."""

import time

import numpy as np
from turboquant import TurboQuantIndex

rng = np.random.default_rng(20260929)
n, d, q, k = 5000, 384, 100, 10
vectors = rng.normal(size=(n, d)).astype(np.float32)
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
queries = vectors[rng.choice(n, size=q, replace=False)] + 0.02 * rng.normal(size=(q, d)).astype(
    np.float32
)
queries /= np.linalg.norm(queries, axis=1, keepdims=True)
exact = np.argsort(-(queries @ vectors.T), axis=1)[:, :k]
for bits in (8, 6, 4):
    t0 = time.perf_counter()
    index = TurboQuantIndex(
        dimension=d, num_bits=bits, use_qjl=True, seed=42, memory_efficient=True
    )
    index.add(vectors)
    build = time.perf_counter() - t0
    t1 = time.perf_counter()
    _, approx = index.search(queries, k=k)
    query = time.perf_counter() - t1
    recall = np.mean([len(set(exact[i]) & set(approx[i])) / k for i in range(q)])
    print(
        f"bits={bits} recall@10={recall:.4f} build_s={build:.3f} query_ms_each={1000 * query / q:.3f} compression={index.compression_ratio:.2f}x"
    )
