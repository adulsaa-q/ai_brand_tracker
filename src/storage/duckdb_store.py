import json
import os

import duckdb
import pandas as pd


class DuckDBStore:
    """DuckDB star-schema store. Single analytical source of truth.

    See docs/adr/0001-single-analytical-store.md for why SQLite was dropped.
    """

    def __init__(self, db_path: str = "data/intelligence.duckdb"):
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_schema()

    def _get_connection(self):
        return duckdb.connect(self.db_path)

    def _init_schema(self):
        with self._get_connection() as con:
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
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_observation (
                    observation_id VARCHAR PRIMARY KEY,
                    run_id VARCHAR,
                    timestamp TIMESTAMP NOT NULL,
                    query_id VARCHAR,
                    vertical VARCHAR,
                    provider VARCHAR NOT NULL,
                    model_name VARCHAR NOT NULL,
                    answer_surface VARCHAR NOT NULL,
                    grounding_enabled BOOLEAN,
                    parse_status VARCHAR,
                    latency_ms INTEGER,
                    token_count INTEGER,
                    response_text VARCHAR
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_brand_mention (
                    mention_id VARCHAR PRIMARY KEY,
                    observation_id VARCHAR NOT NULL,
                    run_id VARCHAR,
                    timestamp TIMESTAMP NOT NULL,
                    query_id VARCHAR NOT NULL,
                    brand_id VARCHAR NOT NULL,
                    brand_name VARCHAR,
                    mentioned BOOLEAN NOT NULL,
                    rank INTEGER,
                    recommendation_intent VARCHAR,
                    sentiment VARCHAR,
                    strengths_json VARCHAR,
                    weaknesses_json VARCHAR
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS fact_citation (
                    citation_id VARCHAR PRIMARY KEY,
                    observation_id VARCHAR NOT NULL,
                    run_id VARCHAR,
                    domain VARCHAR NOT NULL,
                    url VARCHAR,
                    title VARCHAR,
                    source_type VARCHAR
                );
            """)

    # ------------------------------------------------------------------ writes
    def insert_brand(self, brand_id: str, name: str, vertical: str, is_focal: bool = False, aliases=None, domains=None):
        with self._get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO dim_brand
                    (brand_id, name, vertical, is_focal_brand, aliases_json, official_domains_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [brand_id, name, vertical, is_focal, json.dumps(aliases or []), json.dumps(domains or [])],
            )

    def insert_query(self, query: dict):
        with self._get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO dim_query
                    (query_id, text_th, vertical, category, intent, persona_id, is_control_set)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    query["query_id"],
                    query.get("text_th", ""),
                    query.get("vertical_id") or query.get("vertical") or "",
                    query.get("category"),
                    query.get("intent"),
                    query.get("persona_id"),
                    bool(query.get("is_control_set", False)),
                ],
            )

    def insert_observation(self, obs: dict):
        with self._get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO fact_observation
                    (observation_id, run_id, timestamp, query_id, vertical, provider, model_name,
                     answer_surface, grounding_enabled, parse_status, latency_ms, token_count, response_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    obs["observation_id"],
                    obs.get("run_id"),
                    obs["timestamp"],
                    obs["query_id"],
                    obs.get("vertical_id"),
                    obs["provider"],
                    obs["model_name"],
                    obs["answer_surface"],
                    obs.get("grounding_enabled"),
                    obs.get("parse_status"),
                    obs.get("response_latency_ms"),
                    obs.get("token_count"),
                    obs.get("response_raw_text"),
                ],
            )
            for m in obs.get("brand_mentions", []):
                con.execute(
                    """
                    INSERT OR REPLACE INTO fact_brand_mention
                        (mention_id, observation_id, run_id, timestamp, query_id, brand_id, brand_name,
                         mentioned, rank, recommendation_intent, sentiment, strengths_json, weaknesses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        f"{obs['observation_id']}_{m['brand_id']}",
                        obs["observation_id"],
                        obs.get("run_id"),
                        obs["timestamp"],
                        obs["query_id"],
                        m["brand_id"],
                        m.get("brand_name"),
                        m.get("mentioned", False),
                        m.get("rank"),
                        m.get("recommendation_intent"),
                        m.get("sentiment"),
                        json.dumps(m.get("key_strengths_mentioned", [])),
                        json.dumps(m.get("key_weaknesses_mentioned", [])),
                    ],
                )
            for idx, c in enumerate(obs.get("citations", [])):
                con.execute(
                    """
                    INSERT OR REPLACE INTO fact_citation
                        (citation_id, observation_id, run_id, domain, url, title, source_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        f"{obs['observation_id']}_cite_{idx}",
                        obs["observation_id"],
                        obs.get("run_id"),
                        c.get("domain", "web"),
                        c.get("url"),
                        c.get("title"),
                        c.get("source_type", "unknown"),
                    ],
                )

    # ------------------------------------------------------------------- reads
    def get_brands(self, vertical: str | None = None) -> pd.DataFrame:
        with self._get_connection() as con:
            if vertical:
                return con.execute("SELECT * FROM dim_brand WHERE vertical = ?", [vertical]).df()
            return con.execute("SELECT * FROM dim_brand").df()

    def fetch_df(self, sql: str, params: list | None = None) -> pd.DataFrame:
        with self._get_connection() as con:
            return con.execute(sql, params or []).df()

    def count_rows(self, table: str, run_id: str | None = None) -> int:
        allowed = {"dim_brand", "dim_query", "fact_observation", "fact_brand_mention", "fact_citation"}
        if table not in allowed:
            raise ValueError(f"Unknown table: {table}")
        with self._get_connection() as con:
            if run_id and table != "dim_brand" and table != "dim_query":
                row = con.execute(f"SELECT COUNT(*) FROM {table} WHERE run_id = ?", [run_id]).fetchone()
            else:
                row = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return int(row[0]) if row else 0
