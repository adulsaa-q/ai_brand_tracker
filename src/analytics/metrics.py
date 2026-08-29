from collections import defaultdict
from typing import Any


class MarketMetricsEngine:
    @staticmethod
    def calculate_share_of_voice(observations: list[dict[str, Any]]) -> dict[str, Any]:
        total_queries = len(set(obs["query_id"] for obs in observations))
        if total_queries == 0:
            return {}

        brand_mentions = defaultdict(int)
        brand_ranks = defaultdict(list)
        brand_sentiments = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
        brand_intents = defaultdict(lambda: {"recommended": 0, "neutral": 0, "negative": 0})

        for obs in observations:
            for m in obs.get("brand_mentions", []):
                b_name = m["brand_name"]
                if m.get("mentioned", True):
                    brand_mentions[b_name] += 1
                    if m.get("rank"):
                        brand_ranks[b_name].append(m["rank"])
                    s = m.get("sentiment", "neutral")
                    brand_sentiments[b_name][s] += 1

                    intent = m.get("recommendation_intent", "neutral_mention")
                    if intent in ["strongly_recommended", "recommended"]:
                        brand_intents[b_name]["recommended"] += 1
                    elif intent in ["warning_or_caution", "not_recommended"]:
                        brand_intents[b_name]["negative"] += 1
                    else:
                        brand_intents[b_name]["neutral"] += 1

        results = []
        for brand, count in brand_mentions.items():
            mention_rate = (count / total_queries) * 100
            ranks = brand_ranks[brand]
            avg_rank = sum(ranks) / len(ranks) if ranks else None

            s_data = brand_sentiments[brand]
            total_s = sum(s_data.values()) or 1
            net_sentiment_score = ((s_data["positive"] - s_data["negative"]) / total_s) * 100

            i_data = brand_intents[brand]
            total_i = sum(i_data.values()) or 1
            nrs = ((i_data["recommended"] - i_data["negative"]) / total_i) * 100

            results.append(
                {
                    "brand": brand,
                    "mentions": count,
                    "share_of_voice_pct": round(mention_rate, 1),
                    "average_rank": round(avg_rank, 2) if avg_rank else None,
                    "net_sentiment_score": round(net_sentiment_score, 1),
                    "net_recommendation_score": round(nrs, 1),
                    "positive_pct": round((s_data["positive"] / total_s) * 100, 1),
                    "negative_pct": round((s_data["negative"] / total_s) * 100, 1),
                }
            )

        results.sort(key=lambda x: x["share_of_voice_pct"], reverse=True)
        return {"total_queries": total_queries, "brands": results}
