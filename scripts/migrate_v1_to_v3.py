# scripts/migrate_v1_to_v3.py
"""Migrate the legacy v1 results CSV into the DuckDB star schema.

Phase 0 remediation: the SQLite dual-write was removed (see ADR 0001) and the
observation schema now records real provenance (provider / answer_surface).
Legacy rows come from ``gemini-2.5-flash`` with Google Search grounding, so they
map to provider ``google_genai`` / surface ``generative_answer``.
"""

import hashlib
import json
import os

import pandas as pd

from src.storage.duckdb_store import DuckDBStore


def migrate_csv_to_stores(
    csv_path: str = "sample_output/results_sample.csv",
    duckdb_path: str = "data/intelligence.duckdb",
    sqlite_path: str | None = None,  # kept for CLI backward compat; ignored
) -> dict:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}")

    df = pd.read_csv(csv_path)
    store = DuckDBStore(db_path=duckdb_path)
    run_id = "run_legacy_v1_import"

    for brand in df["brand"].dropna().unique():
        brand_id = brand.lower().replace(" ", "_")
        store.insert_brand(
            brand_id=brand_id,
            name=brand,
            vertical="ecommerce_retail_th",
            is_focal=brand.lower() in {"shopee", "konvy"},
        )

    obs_count = mention_count = citation_count = 0
    for (ts, prompt_text, model), group in df.groupby(["timestamp", "prompt", "model"]):
        query_hash = hashlib.md5(prompt_text.encode("utf-8")).hexdigest()[:12]
        query_id = f"q_hist_{query_hash}"
        category = group["prompt_category"].iloc[0] if pd.notna(group["prompt_category"].iloc[0]) else "general"
        store.insert_query(
            {
                "query_id": query_id,
                "text_th": prompt_text,
                "vertical_id": "ecommerce_retail_th",
                "category": category,
                "intent": "recommendation_discovery",
                "is_control_set": True,
            }
        )

        obs_id = f"obs_hist_{query_hash}"
        mentions, citations = [], []
        seen_domains: set[str] = set()
        for _, row in group.iterrows():
            brand_name = row["brand"]
            mentioned = str(row["mentioned"]).strip().lower() in {"1", "true"}
            rank = int(row["rank"]) if pd.notna(row["rank"]) and row["rank"] > 0 else None
            sentiment = str(row["sentiment"]).strip().lower() if pd.notna(row["sentiment"]) else "neutral"
            if sentiment not in {"positive", "neutral", "negative"}:
                sentiment = "neutral"
            reason = str(row["reason"]) if pd.notna(row["reason"]) else ""
            mentions.append(
                {
                    "brand_id": brand_name.lower().replace(" ", "_"),
                    "brand_name": brand_name,
                    "mentioned": mentioned,
                    "rank": rank,
                    "recommendation_intent": "recommended" if mentioned and (rank or 99) <= 2 else "neutral_mention",
                    "sentiment": sentiment,
                    "key_strengths_mentioned": [reason] if reason and sentiment == "positive" else [],
                    "key_weaknesses_mentioned": [reason] if reason and sentiment == "negative" else [],
                }
            )
            mention_count += 1
            sources = row.get("sources")
            if pd.notna(sources) and isinstance(sources, str):
                for d in (s.strip() for s in sources.split(",") if s.strip()):
                    if d in seen_domains:
                        continue
                    seen_domains.add(d)
                    citations.append({"domain": d, "source_type": "news"})
                    citation_count += 1

        store.insert_observation(
            {
                "observation_id": obs_id,
                "run_id": run_id,
                "timestamp": str(ts),
                "query_id": query_id,
                "vertical_id": "ecommerce_retail_th",
                "provider": "google_genai",
                "model_name": str(model),
                "answer_surface": "generative_answer",
                "grounding_enabled": True,
                "parse_status": "not_applicable",
                "response_latency_ms": None,
                "response_raw_text": f"[legacy v1 import] {prompt_text}",
                "brand_mentions": mentions,
                "citations": citations,
            }
        )
        obs_count += 1

    result = {"observations": obs_count, "mentions": mention_count, "citations": citation_count}
    print(f"Migration complete: {json.dumps(result)}")
    return result


if __name__ == "__main__":
    migrate_csv_to_stores()
