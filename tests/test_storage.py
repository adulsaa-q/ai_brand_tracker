from src.storage.duckdb_store import DuckDBStore


def test_duckdb_store_initialization(tmp_path):
    test_db = str(tmp_path / "test_intel.duckdb")
    store = DuckDBStore(db_path=test_db)
    
    # Test brand insertion
    store.insert_brand(
        brand_id="shopee",
        name="Shopee Thailand",
        vertical="ecommerce",
        is_focal=True,
        aliases=["ช้อปปี้"],
        domains=["shopee.co.th"]
    )
    
    df = store.get_brands(vertical="ecommerce")
    assert len(df) == 1
    assert df.iloc[0]["name"] == "Shopee Thailand"
    assert df.iloc[0]["is_focal_brand"]
