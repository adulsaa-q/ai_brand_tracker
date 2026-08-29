import json
import os
import sqlite3
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: str = "data/intelligence.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_schema()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_schema(self):
        with self._get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_brand (
                    brand_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    vertical TEXT NOT NULL,
                    is_focal_brand INTEGER DEFAULT 0,
                    aliases_json TEXT,
                    official_domains_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_query (
                    query_id TEXT PRIMARY KEY,
                    text_th TEXT NOT NULL,
                    vertical TEXT NOT NULL,
                    category TEXT,
                    intent TEXT,
                    persona_id TEXT,
                    is_control_set INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fact_observation (
                    observation_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    query_id TEXT,
                    engine_provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    latency_ms INTEGER,
                    response_text TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fact_brand_mention (
                    mention_id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    query_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    mentioned INTEGER NOT NULL,
                    rank INTEGER,
                    recommendation_intent TEXT,
                    sentiment TEXT,
                    strengths_json TEXT,
                    weaknesses_json TEXT
                );
            """)
            con.commit()

    def insert_brand(self, brand_id: str, name: str, vertical: str, is_focal: bool = False, aliases=None, domains=None):
        with self._get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO dim_brand (brand_id, name, vertical, is_focal_brand, aliases_json, official_domains_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (brand_id, name, vertical, 1 if is_focal else 0, json.dumps(aliases or []), json.dumps(domains or [])))
            con.commit()

    def get_brands(self, vertical: str | None = None) -> list[dict[str, Any]]:
        with self._get_connection() as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            if vertical:
                cur.execute("SELECT * FROM dim_brand WHERE vertical = ?", (vertical,))
            else:
                cur.execute("SELECT * FROM dim_brand")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
