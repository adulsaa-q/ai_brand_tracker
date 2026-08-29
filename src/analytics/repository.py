# src/analytics/repository.py
"""Read side of the analytical store.

Phase 2 remediation: analytics used to run on the in-memory list the runner
built during a scan. That list is now written to DuckDB and read back here, so
DuckDB is the canonical source and analytics reflect exactly what was persisted
(a dropped mention shows up as dropped, not silently present).
"""

from __future__ import annotations

import json
from typing import Any

from src.storage import DuckDBStore


class AnalyticsRepository:
    def __init__(self, store: DuckDBStore):
        self.store = store

    def load_observations(self, run_id: str) -> list[dict[str, Any]]:
        """Reconstruct observation dicts (the shape the analytics functions expect)
        by joining fact_observation -> dim_query -> fact_brand_mention / fact_citation."""
        obs_df = self.store.fetch_df(
            """
            SELECT o.observation_id, o.run_id, o.query_id, o.provider, o.answer_surface,
                   o.parse_status, o.response_text, o.timestamp, o.vertical,
                   q.text_th AS query_text, q.category, q.is_control_set
            FROM fact_observation o
            LEFT JOIN dim_query q USING (query_id)
            WHERE o.run_id = ?
            ORDER BY o.observation_id
            """,
            [run_id],
        )
        if obs_df.empty:
            return []

        mentions_df = self.store.fetch_df(
            "SELECT * FROM fact_brand_mention WHERE run_id = ? ORDER BY observation_id, mention_id", [run_id]
        )
        citations_df = self.store.fetch_df(
            "SELECT * FROM fact_citation WHERE run_id = ? ORDER BY observation_id, citation_id", [run_id]
        )

        mentions_by_obs: dict[str, list[dict]] = {}
        for r in mentions_df.to_dict("records"):
            mentions_by_obs.setdefault(r["observation_id"], []).append(
                {
                    "brand_id": r["brand_id"],
                    "brand_name": r["brand_name"],
                    "mentioned": bool(r["mentioned"]),
                    "rank": None
                    if r["rank"] is None or (isinstance(r["rank"], float) and r["rank"] != r["rank"])
                    else int(r["rank"]),
                    "recommendation_intent": r["recommendation_intent"],
                    "sentiment": r["sentiment"],
                    "key_strengths_mentioned": json.loads(r["strengths_json"] or "[]"),
                    "key_weaknesses_mentioned": json.loads(r["weaknesses_json"] or "[]"),
                    "price_or_deal_claims": [],
                }
            )

        citations_by_obs: dict[str, list[dict]] = {}
        for r in citations_df.to_dict("records"):
            citations_by_obs.setdefault(r["observation_id"], []).append(
                {"domain": r["domain"], "url": r["url"], "title": r["title"], "source_type": r["source_type"]}
            )

        observations = []
        for r in obs_df.to_dict("records"):
            oid = r["observation_id"]
            observations.append(
                {
                    "observation_id": oid,
                    "run_id": r["run_id"],
                    "query_id": r["query_id"],
                    "query_text": r["query_text"] or "",
                    "provider": r["provider"],
                    "answer_surface": r["answer_surface"],
                    "parse_status": r["parse_status"],
                    "category": r["category"] or "General",
                    "is_control_set": bool(r["is_control_set"]) if r["is_control_set"] is not None else False,
                    "response_raw_text": r["response_text"] or "",
                    "vertical_id": r["vertical"],
                    "brand_mentions": mentions_by_obs.get(oid, []),
                    "citations": citations_by_obs.get(oid, []),
                }
            )
        return observations
