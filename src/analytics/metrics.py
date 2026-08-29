from collections import defaultdict
from typing import Any

# Phase 2: SoV / NRS are generative-answer concepts ("did the AI recommend you").
# A SERP position or a retrieval hit is a different kind of signal, so metrics are
# computed per answer_surface and the headline numbers use PRIMARY_SURFACE only.
PRIMARY_SURFACE = "generative_answer"
_RECO_INTENTS = {"strongly_recommended", "recommended"}
_NEG_INTENTS = {"warning_or_caution", "not_recommended"}


class MarketMetricsEngine:
    @staticmethod
    def calculate_share_of_voice(observations: list[dict[str, Any]], surface: str | None = None) -> dict[str, Any]:
        if surface is not None:
            observations = [o for o in observations if o.get("answer_surface") == surface]

        total_queries = len({obs["query_id"] for obs in observations})
        if total_queries == 0:
            return {"total_queries": 0, "brands": [], "surface": surface}

        brand_mentions: dict[str, int] = defaultdict(int)
        brand_ranks: dict[str, list[int]] = defaultdict(list)
        brand_sentiments = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
        brand_intents = defaultdict(lambda: {"recommended": 0, "neutral": 0, "negative": 0})

        for obs in observations:
            for m in obs.get("brand_mentions", []):
                if not m.get("mentioned", True):
                    continue
                name = m["brand_name"]
                brand_mentions[name] += 1
                if m.get("rank"):
                    brand_ranks[name].append(m["rank"])
                brand_sentiments[name][m.get("sentiment", "neutral")] += 1
                intent = m.get("recommendation_intent", "neutral_mention")
                if intent in _RECO_INTENTS:
                    brand_intents[name]["recommended"] += 1
                elif intent in _NEG_INTENTS:
                    brand_intents[name]["negative"] += 1
                else:
                    brand_intents[name]["neutral"] += 1

        results = []
        for brand, count in brand_mentions.items():
            ranks = brand_ranks[brand]
            avg_rank = round(sum(ranks) / len(ranks), 2) if ranks else None

            s = brand_sentiments[brand]
            total_s = sum(s.values()) or 1
            net_sentiment = round(((s["positive"] - s["negative"]) / total_s) * 100, 1)

            i = brand_intents[brand]
            total_i = sum(i.values()) or 1
            nrs = round(((i["recommended"] - i["negative"]) / total_i) * 100, 1)

            results.append(
                {
                    "brand": brand,
                    "mentions": count,
                    "share_of_voice_pct": round((count / total_queries) * 100, 1),
                    "average_rank": avg_rank,
                    "net_sentiment_score": net_sentiment,
                    "net_recommendation_score": nrs,
                    "positive_pct": round((s["positive"] / total_s) * 100, 1),
                    "negative_pct": round((s["negative"] / total_s) * 100, 1),
                }
            )

        # deterministic: SoV desc, then brand name asc for stable tie-breaking
        results.sort(key=lambda x: (-x["share_of_voice_pct"], x["brand"]))
        return {"total_queries": total_queries, "brands": results, "surface": surface}

    @classmethod
    def build_report(cls, observations: list[dict[str, Any]]) -> dict[str, Any]:
        """Headline metrics (primary surface) plus a per-surface breakdown."""
        surfaces = sorted({o.get("answer_surface", "unknown") for o in observations})
        by_surface = {s: cls.calculate_share_of_voice(observations, surface=s) for s in surfaces}

        primary = by_surface.get(PRIMARY_SURFACE)
        if primary is None:
            # no generative surface in this run - fall back to whichever surface exists
            primary = cls.calculate_share_of_voice(observations)
            primary_surface = "all_surfaces_combined"
        else:
            primary_surface = PRIMARY_SURFACE

        return {
            "primary_surface": primary_surface,
            "total_queries": primary["total_queries"],
            "brands": primary["brands"],
            "surfaces_present": surfaces,
            "by_surface": by_surface,
        }
