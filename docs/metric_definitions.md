# Metric definitions

What each metric means, **exactly as implemented** in `src/analytics/`. Where an
older blueprint proposed a different formula, that is noted so the gap is visible
(MASTER_PROMPT §25 asks for this).

All metrics are computed **per `answer_surface`** and the headline figures use
`generative_answer` only — see [ADR 0002](adr/0002-engine-surfaces-and-temporal-context.md).

---

## Share of Voice (SoV)

```
SoV(brand) = mentioned_query_count(brand) / distinct_query_count  × 100
```

- `mentioned_query_count` — queries where the brand's `mentioned` flag is true
  (one count per query, not per mention).
- `distinct_query_count` — distinct `query_id` in the surface's observation set.
- Range 0–100. "How often does this surface bring the brand up at all."
- **Limitation:** presence, not endorsement. A brand named only to warn against
  it still scores. Pair with NRS.
- Source: `MarketMetricsEngine.calculate_share_of_voice`.

## Average rank

```
average_rank(brand) = mean(rank) over mentions where rank is not null
```

- For `generative_answer`: the model's recommendation position.
- For `organic_serp`: the Google result position. **Not comparable across
  surfaces** — never averaged together.
- Lower is better. Null when the brand is mentioned but unranked.

## Net Sentiment Score

```
net_sentiment(brand) = (positive_mentions − negative_mentions) / total_mentions × 100
```

- `sentiment ∈ {positive, neutral, negative}` from the model's structured output.
- Range −100..+100.
- Shown as `n/a` in the dashboard for `organic_serp` / `web_retrieval` — those
  surfaces carry no sentiment signal (the engine does not fabricate one).

## Net Recommendation Score (NRS)

```
recommended = count(recommendation_intent ∈ {strongly_recommended, recommended})
negative    = count(recommendation_intent ∈ {not_recommended, warning_or_caution})
NRS(brand)  = (recommended − negative) / total_intent_mentions × 100
```

- Range −100..+100. "When named, is the brand endorsed or cautioned against."
- **Blueprint discrepancy:** [`archive/MASTER_BLUEPRINT_V3.md`](archive/MASTER_BLUEPRINT_V3.md)
  §6.2 proposed a rank-weighted form,
  `mean( w_intent · 1/√rank · sentiment_weight )`. That is
  **not implemented** — the current formula is unweighted intent balance. If the
  rank-weighted version is wanted, it needs its own ADR (weights need evidence,
  MASTER_PROMPT §25).

## Grounded response rate

```
grounded_rate = observations_with_≥1_citation / total_observations × 100
```

- A measurement, not an estimate. Replaces the removed "0–2 day information lag"
  figure, which was fabricated from this same ratio.
- Source: `AIInformationLagTracker.measure_knowledge_freshness`.

## Citation influence (per domain)

```
influence_share(domain) = citations_from_domain / total_citations × 100
top_associated_brand    = brand most often mentioned in the same observation
```

- **Not yet** the `influence × relevance × authority × controllability` score
  that MASTER_PROMPT §16 calls for. No first-seen / last-seen tracking yet.
- Source: `CitationInfluenceAnalyzer.analyze_influence`.

## Opportunity confidence

- `OpportunityFinder` emits category-level visibility gaps with a `confidence`
  label (`LOW` / `MEDIUM`) derived from how many queries in a category missed the
  focal brand. It is **not** a calibrated probability and **not** a 0–100
  opportunity score (MASTER_PROMPT §26 wants the latter).

---

## Not yet defined (tracked in `MASTER_PROMPT_COVERAGE.md`)

Recommendation Strength, Citation Authority, Competitor Threat, Content
Opportunity, Reputation Score, AI Accuracy Score, Trend Opportunity, Social /
Commerce Momentum, Engine Consensus, Volatility. Each needs formula, rationale,
normalization, weighting, evidence, limitations, sensitivity before it ships.
