# scripts/migrate_v1_to_v3.py
import hashlib
import json
import os

import pandas as pd

from src.storage.duckdb_store import DuckDBStore
from src.storage.sqlite_store import SQLiteStore


def migrate_csv_to_stores(
    csv_path="sample_output/results_sample.csv",
    duckdb_path="data/intelligence.duckdb",
    sqlite_path="data/intelligence.db",
):
    """Migrate historical v1/v2 results CSV into DuckDB Star Schema and SQLite."""
    print(f"📦 Starting Historical Data Migration from {csv_path}...")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} historical rows.")

    duckdb_store = DuckDBStore(db_path=duckdb_path)
    sqlite_store = SQLiteStore(db_path=sqlite_path)

    # 1. Insert Brands into dim_brand
    unique_brands = df["brand"].dropna().unique()
    for brand in unique_brands:
        brand_id = brand.lower().replace(" ", "_")
        is_focal = brand.lower() in ["shopee", "konvy"]
        duckdb_store.insert_brand(brand_id=brand_id, name=brand, vertical="ecommerce_beauty", is_focal=is_focal)
        sqlite_store.insert_brand(brand_id=brand_id, name=brand, vertical="ecommerce_beauty", is_focal=is_focal)
    print(f"✅ Migrated {len(unique_brands)} unique brands into dim_brand.")

    # 2. Insert Queries and Observations
    grouped = df.groupby(["timestamp", "prompt", "model"])
    obs_count = 0
    mention_count = 0
    citation_count = 0

    with duckdb_store._get_connection() as con_duck:
        for (ts, prompt_text, model), group in grouped:
            obs_count += 1
            query_hash = hashlib.md5(prompt_text.encode("utf-8")).hexdigest()[:12]
            query_id = f"q_hist_{query_hash}"
            category = group["prompt_category"].iloc[0] if pd.notna(group["prompt_category"].iloc[0]) else "general"

            # Insert Query
            con_duck.execute(
                """
                INSERT OR REPLACE INTO dim_query (query_id, text_th, vertical, category, intent, is_control_set)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                [query_id, prompt_text, "ecommerce_beauty", category, "recommendation_discovery", True],
            )

            obs_id = f"obs_hist_{obs_count}_{query_hash}"
            con_duck.execute(
                """
                INSERT OR REPLACE INTO fact_observation (observation_id, timestamp, query_id, engine_provider, model_name, latency_ms, response_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                [obs_id, ts, query_id, "google_gemini", str(model), 1500, f"Historical response for: {prompt_text}"],
            )

            # Process mentions in this group
            for _, row in group.iterrows():
                mention_count += 1
                brand_name = row["brand"]
                brand_id = brand_name.lower().replace(" ", "_")
                mentioned = bool(
                    row["mentioned"] == 1 or row["mentioned"] is True or str(row["mentioned"]).lower() == "true"
                )
                rank = int(row["rank"]) if pd.notna(row["rank"]) and row["rank"] > 0 else None
                sentiment = str(row["sentiment"]) if pd.notna(row["sentiment"]) else "neutral"
                reason = str(row["reason"]) if pd.notna(row["reason"]) else ""

                mention_id = f"m_{obs_id}_{brand_id}"
                strengths_json = json.dumps([reason] if reason and sentiment == "positive" else [])
                weaknesses_json = json.dumps([reason] if reason and sentiment == "negative" else [])

                con_duck.execute(
                    """
                    INSERT OR REPLACE INTO fact_brand_mention (mention_id, observation_id, timestamp, query_id, brand_id, mentioned, rank, recommendation_intent, sentiment, strengths_json, weaknesses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    [
                        mention_id,
                        obs_id,
                        ts,
                        query_id,
                        brand_id,
                        mentioned,
                        rank,
                        "recommended" if mentioned and (rank or 1) <= 2 else "neutral_mention",
                        sentiment,
                        strengths_json,
                        weaknesses_json,
                    ],
                )

                # Process citations if available
                sources_str = row.get("sources")
                if pd.notna(sources_str) and isinstance(sources_str, str) and sources_str.strip():
                    domains = [d.strip() for d in sources_str.split(",") if d.strip()]
                    for d in domains:
                        citation_count += 1
                        cite_id = f"c_{obs_id}_{hashlib.md5(d.encode()).hexdigest()[:8]}"
                        con_duck.execute(
                            """
                            INSERT OR REPLACE INTO fact_citation (citation_id, observation_id, domain, source_type)
                            VALUES (?, ?, ?, ?)
                        """,
                            [cite_id, obs_id, d, "news" if "news" in d or "ditp" in d else "marketplace"],
                        )

    print(
        f"🎉 Migration Complete: {obs_count} Observations, {mention_count} Brand Mentions, {citation_count} Citations persisted to DuckDB & SQLite."
    )


if __name__ == "__main__":
    os.makedirs("scripts", exist_ok=True)
    migrate_csv_to_stores()
