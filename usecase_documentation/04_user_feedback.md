# 04 — User Feedback

## 1. Purpose

This document records feedback from evaluators who review the recommendation strategies in MUSICALLY.

Evaluators are team members/product or engineering stakeholders judging retrieval quality, not assumed end consumers.

Feedback is collected through the Streamlit comparison interface and stored automatically whenever an evaluator selects 👍 or 👎.

> **Important:** This document should contain actual feedback only after testing begins. Until then, the tables below are templates.

## 2. Feedback fields

For every recommendation, the system records:

| Field | Meaning |
|---|---|
| `query_song` | Seed song selected by the evaluator |
| `strategy` | Strategy that generated the recommendation |
| `recommended_song` | Song being evaluated |
| `vote` | `relevant` or `not_relevant` |
| `evaluator` | Evaluator identifier |
| `timestamp` | Time feedback was submitted |

The evaluator does **not** manually fill this table.

## 3. How the entry is created automatically

**Evaluator selects seed song**
→ **MUSICALLY runs all configured strategies**
→ **Recommendations appear side by side**
→ **Evaluator clicks 👍 / 👎**
→ **Streamlit captures the click**
→ **Application creates one feedback record**
→ **Record is appended to `data/feedback.csv` (or stored in SQLite)**
→ **Aggregate relevance rate is recalculated/displayed**

Example:

```text
query_song = Believer
strategy = global_cosine
recommended_song = Song A
vote = relevant
evaluator = evaluator_01
timestamp = 2026-09-16 14:30:21
```

No manual editing of this document is required for each vote.

## 4. Feedback storage

Recommended initial implementation:

`data/feedback.csv`

Schema:

```text
query_song,strategy,recommended_song,vote,evaluator,timestamp
```

Example:

```text
Believer,global_cosine,Song A,relevant,evaluator_01,2026-09-16 14:30:21
Believer,global_cosine,Song B,not_relevant,evaluator_01,2026-09-16 14:30:28
Believer,kmeans,Song C,relevant,evaluator_01,2026-09-16 14:31:04
```

The application appends a new row whenever a vote is submitted.

SQLite can be used later if the feedback volume grows.

## 5. Per-strategy relevance log

Populate this section from actual stored feedback after testing.

| Date | Query song | Strategy | Relevant? | Evaluator | Notes |
|---|---|---|---|---|---|
| | | Cluster-restricted KMeans | | | |
| | | Global cosine similarity | | | |
| | | Genre-filtered | | | |

`Notes` should contain only observations actually provided by the evaluator.

## 6. Questions for evaluators

### Understanding what “relevant” means

1. What makes a recommendation relevant — same genre, sound/mood, era, or something else?
2. Should the comparison prioritize relevance, diversity, novelty, or a combination?
3. What kind of recommendation would make you reject a strategy?

### After a comparison round

- Which recommendations were clearly relevant?
- Which were clearly wrong?
- Was any strategy's output surprising?
- Did one strategy consistently produce more relevant results?
- Were there cases where a strategy was diverse but less relevant?
- Did the synthetic dataset expose meaningful differences?
- Were any results too noisy or ambiguous to judge?

## 7. Open questions / decisions

| Date | Question | Response | Impact |
|---|---|---|---|
| | | | |

Record only actual questions, responses, and resulting decisions.

## 8. Aggregate evaluation

The application calculates:

**Relevance Rate = Relevant recommendations / Total evaluated recommendations**

| Strategy | Relevant | Evaluated | Relevance rate |
|---|---:|---:|---:|
| Cluster-restricted KMeans | — | — | — |
| Global cosine | — | — | — |
| Genre-filtered | — | — | — |

These values must come from actual stored feedback, not manual estimates.

## 9. Limitations

This evaluation uses a synthetic dataset and human evaluator judgments.

Therefore:

- Results are directional.
- Relevance judgments can be subjective.
- Results do not represent actual user satisfaction.
- Results are not a production benchmark.
- A higher relevance rate in this evaluation does not automatically mean the same strategy will perform better on a real music catalog.

## 10. Feedback → next iteration

**Feedback**
→ **Aggregate results**
→ **Identify strengths/problems**
→ **Discuss with team**
→ **Decide whether to keep, modify, or add a strategy**
→ **Update PRD/solutioning**
→ **Run another comparison round**

Every resulting decision should be documented with the evidence behind it.
