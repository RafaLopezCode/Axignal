from __future__ import annotations

import pytest

from tools.runtime.eb08_product_proof import run_store_load_harness


@pytest.mark.parametrize("organization_count", [1, 2, 100])
def test_eb08_store_load_recovery_and_isolation(tmp_path, organization_count: int) -> None:
    result = run_store_load_harness(
        tmp_path / f"product-proof-{organization_count}.sqlite3",
        organization_count=organization_count,
    )

    assert result.organization_count == organization_count
    assert result.recovered_count == organization_count
    assert result.backup_recovered_count == organization_count
    assert result.isolated is True
    assert result.database_bytes > 0
    assert result.backup_bytes > 0
    assert result.write_ms >= 0
    assert result.read_ms >= 0
    assert result.backup_ms >= 0
