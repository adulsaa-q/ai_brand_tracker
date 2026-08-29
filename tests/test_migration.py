import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.migrate_v1_to_v3 import migrate_csv_to_stores
from src.storage.duckdb_store import DuckDBStore


def test_migration_pipeline(tmp_path):
    test_duckdb = str(tmp_path / "test_intel.duckdb")
    test_sqlite = str(tmp_path / "test_intel.db")
    
    migrate_csv_to_stores(
        csv_path="sample_output/results_sample.csv",
        duckdb_path=test_duckdb,
        sqlite_path=test_sqlite
    )
    
    store = DuckDBStore(db_path=test_duckdb)
    brands = store.get_brands()
    assert len(brands) == 9
    assert "Shopee" in brands["name"].values
