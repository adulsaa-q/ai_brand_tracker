"""Test isolation.

Phase 0 remediation: tests used to POST to /api/v1/verticals, which wrote the
real ``config/entities.yaml`` (that is how ``test_luxury_watch_th`` ended up
committed). Every test now runs against a throwaway copy of the config and a
temporary data directory. Nothing under the repo working tree is mutated.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_TMP = tempfile.mkdtemp(prefix="aibt_tests_")
_ENTITIES = os.path.join(_TMP, "entities.yaml")
_DATA = os.path.join(_TMP, "data")

shutil.copy(os.path.join(_REPO, "config", "entities.yaml"), _ENTITIES)
os.makedirs(_DATA, exist_ok=True)

# Must be set before src.api / src.runner are imported (they read these once).
os.environ["ENTITIES_PATH"] = _ENTITIES
os.environ["DATA_DIR"] = _DATA

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seed_reference_scan():
    """Give metrics/export endpoints something real to read."""
    from src.runner import run_intelligence_pipeline

    run_intelligence_pipeline(
        vertical_id="ecommerce_retail_th",
        count=6,
        engine_type="mock",
        include_control=True,
        entities_path=_ENTITIES,
        output_dir=_DATA,
    )
    yield


@pytest.fixture
def tmp_entities_path():
    return _ENTITIES


@pytest.fixture
def tmp_data_dir():
    return _DATA
