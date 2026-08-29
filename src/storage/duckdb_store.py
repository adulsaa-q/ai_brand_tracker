import json
import os

import duckdb
import pandas as pd


class DuckDBStore:
    def __init__(self, db_path: str = "data/intelligence.duckdb"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_schema()

    def _get_connection(self):
        return duckdb.connect(self.db_path)

    def _init_schema(self):
        with self._get_connection() as con:
            # Dimension: Brands
            con.execute("""
                CREATE TABLE IF NOT EXISTS dim_brand (
                    brand_id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    vertical VARCHAR NOT NULL,
                    is_focal_brand BOOLEAN DEFAULT FALSE,
                    aliases_json VARCHAR,
                    official_domains_json VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Dimension: Queries
            con.execute("""
                CREATE TABLE IF NOT EXISTS dim_query (
                    query_id VARCHAR PRIMARY KEY,
                    text_th VARCHAR NOT NULL,
                    vertical VARCHAR NOT NULL,
                    category VARCHAR,
                    intent VARCHAR,
                    persona_id VARCHAR,
                    is_control_set BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Fact: Observations
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_observation (
                    observation_id VARCHAR PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    query_id VARCHAR,
                    engine_provider VARCHAR NOT NULL,
                    model_name VARCHAR NOT NULL,
                    latency_ms INTEGER,
                    response_text VARCHAR
                );
            """)

            # Fact: Brand Mentions (Grain: 1 row per observation x brand)
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_brand_mention (
                    mention_id VARCHAR PRIMARY KEY,
                    observation_id VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    query_id VARCHAR NOT NULL,
                    brand_id VARCHAR NOT NULL,
                    mentioned BOOLEAN NOT NULL,
                    rank INTEGER,
                    recommendation_intent VARCHAR,
                    sentiment VARCHAR,
                    strengths_json VARCHAR,
                    weaknesses_json VARCHAR
                );
            """)

            # Fact: Citations
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_citation (
                    citation_id VARCHAR PRIMARY KEY,
                    observation_id VARCHAR NOT NULL,
                    domain VARCHAR NOT NULL,
                    url VARCHAR,
                    title VARCHAR,
                    source_type VARCHAR
                );
            """)

    def insert_brand(self, brand_id: str, name: str, vertical: str, is_focal: bool = False, aliases=None, domains=None):
        with self._get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO dim_brand (brand_id, name, vertical, is_focal_brand, aliases_json, official_domains_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                [brand_id, name, vertical, is_focal, json.dumps(aliases or []), json.dumps(domains or [])],
            )

    def get_brands(self, vertical: str | None = None) -> pd.DataFrame:
        with self._get_connection() as con:
            if vertical:
                return con.execute("SELECT * FROM dim_brand WHERE vertical = ?", [vertical]).df()
            return con.execute("SELECT * FROM dim_brand").df()

    def insert_observation(self, obs: dict):
        with self._get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO fact_observation (observation_id, timestamp, query_id, engine_provider, model_name, latency_ms, response_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    obs["observation_id"],
                    obs["timestamp"],
                    obs["query_id"],
                    obs["engine_provider"],
                    obs["model_name"],
                    obs.get("response_latency_ms"),
                    obs.get("response_raw_text"),
                ],
            )
            for m in obs.get("brand_mentions", []):
                mention_id = f"{obs['observation_id']}_{m['brand_id']}"
                con.execute(
                    """
                    INSERT OR REPLACE INTO fact_brand_mention (mention_id, observation_id, timestamp, query_id, brand_id, mentioned, rank, recommendation_intent, sentiment, strengths_json, weaknesses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    [
                        mention_id,
                        obs["observation_id"],
                        obs["timestamp"],
                        obs["query_id"],
                        m["brand_id"],
                        m.get("mentioned", False),
                        m.get("rank"),
                        m.get("recommendation_intent"),
                        m.get("sentiment"),
                        json.dumps(m.get("key_strengths_mentioned", [])),
                        json.dumps(m.get("key_weaknesses_mentioned", [])),
                    ],
                )
            for idx, c in enumerate(obs.get("citations", [])):
                citation_id = f"{obs['observation_id']}_cite_{idx}"
                con.execute(
                    """
                    INSERT OR REPLACE INTO fact_citation (citation_id, observation_id, domain, url, title, source_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    [
                        citation_id,
                        obs["observation_id"],
                        c.get("domain", "web"),
                        c.get("url"),
                        c.get("title"),
                        c.get("source_type", "web"),
                    ],
                )
