"""P07: rebuilding the curated store twice gives identical content hashes."""

import pytest

from esw.config import get_settings
from esw.runlog import parquet_content_hash

pytestmark = pytest.mark.slow


def test_rebuild_twice_identical():
    from esw.curate.build import rebuild

    st = get_settings()
    if not (st.path("staged") / "in_bhav" / "in_bhav_nse.parquet").exists():
        pytest.skip("staged data not present")
    rebuild(st)
    h1 = {p.name: parquet_content_hash(p) for p in sorted(st.path("curated").glob("*.parquet"))}
    rebuild(st)
    h2 = {p.name: parquet_content_hash(p) for p in sorted(st.path("curated").glob("*.parquet"))}
    assert h1 == h2 and len(h1) >= 14
