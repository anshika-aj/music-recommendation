# 04 — User Feedback

## 1. Purpose

This document records feedback from evaluators who review the recommendation strategies in MUSICALLY.

Evaluators are team members/product or engineering stakeholders judging retrieval quality, not assumed end consumers.

Feedback is collected through the live Streamlit app and stored automatically in Supabase whenever an evaluator clicks 👍 or 👎.

> **Status:** live and collecting real feedback (not simulated). Vote
> counts are still low — see §5 for the current snapshot. Sections below
> marked "populate as data grows" are genuinely incomplete, not filled
> with placeholder numbers.

## 2. Feedback fields

For every recommendation, the system records:

| Field | Meaning |
|---|---|
| `query_song` | Seed song selected by the evaluator |
| `strategy` | Which of the 5 strategies generated this recommendation |
| `recommended_song` | Song being evaluated ("Track — Artist") |
| `vote` | `relevant` or `not_relevant` |
| `evaluator` | Auto-generated per-browser-session ID (see §3) |
| `created_at` | Timestamp, set automatically by Supabase |

The evaluator does **not** manually fill this table — every row above is written by the app.

## 3. How a vote becomes a record

**Evaluator picks a strategy from the sidebar**
→ **Evaluator selects a seed song and searches**
→ **Recommendations appear, tagged with the active strategy**
→ **Evaluator clicks 👍 / 👎 on a result**
→ **`log_feedback()` inserts one row into the Supabase `feedback` table**
→ **Aggregate relevance rate (§8) is recalculated on next view**

**On the `evaluator` field specifically:** earlier in this project, every
row was logged with the same hardcoded value (`evaluator_01`) because of
a bug in a sidebar input — this was caught by checking the live Supabase
table directly and seeing every row identical. It's now fixed: on first
load, the app generates a random ID (`evaluator_<8 hex chars>`) and stores
it in the browser session, so distinct sessions produce distinct IDs
automatically. This is **session-level**, not person-level — the same
person voting from two different tabs/devices will show up as two
evaluators. See §9 for why this is an accepted limitation for now.

## 4. Feedback storage

**Supabase** (hosted Postgres) — not a local CSV. This matters because
Streamlit Community Cloud's filesystem is ephemeral: a CSV file would be
silently wiped on every app restart or redeploy. Supabase persists
independently of the app's own lifecycle.

Table: `feedback`, columns as in §2, with Row-Level Security policies
controlling read/write access. Accessed from `utils/feedback.py` via the
`supabase-py` client.

## 5. Current snapshot

As of the last check, the table held a small number of real votes — all
logged under the `global_cosine` strategy, all against one query song
("Ab — The Local Train"), roughly evenly split between `relevant` and
`not_relevant`. This is an early sanity-check sample confirming the
pipeline works end-to-end — **not** a representative comparison yet. The
tables in §7 and §8 stay unpopulated until there's enough spread across
strategies and query songs to say something real.

## 6. Questions for evaluators

### Understanding what "relevant" means

1. What makes a recommendation relevant — same genre, sound/mood, era, or something else?
2. Should the comparison prioritize relevance, diversity, novelty, or a combination?
3. What kind of recommendation would make you reject a strategy?

### After a comparison round

- Which recommendations were clearly relevant?
- Which were clearly wrong?
- Was any strategy's output surprising?
- Did one strategy consistently produce more relevant results?
- Were there cases where a strategy was diverse but less relevant?
- Did genre/cluster restriction expose meaningful differences from global search?
- Were any results too noisy or ambiguous to judge?

## 7. Open questions / decisions

| Date | Question | Response | Impact |
|---|---|---|---|
| | | | |

Record only actual questions, responses, and resulting decisions — populate as they happen.

## 8. Aggregate evaluation

The app calculates, live, from Supabase:

**Relevance Rate = Relevant recommendations / Total evaluated recommendations**

| Strategy | Relevant | Evaluated | Relevance rate |
|---|---:|---:|---:|
| `global_cosine` | — | — | — |
| `genre_filtered` | — | — | — |
| `kmeans_restricted` | — | — | — |
| `popularity_weighted` | — | — | — |
| `hybrid` | — | — | — |

To be filled from real stored feedback once there's a meaningful spread
across all 5 strategies and multiple query songs — not from the early
sanity-check sample in §5.

## 9. Limitations

- Results are directional, not a production benchmark.
- Relevance judgments are subjective and evaluator-dependent.
- `evaluator` identifies a browser session, not a person — the same
  person voting from multiple sessions appears as multiple evaluators.
  Acceptable at current scale; would need a real login/identity step to
  fix properly if evaluator count grows.
- The dataset is a real but bounded subset of Spotify's catalog (~81k
  tracks, 114 genres) — not the full catalog, and not production
  engagement data (clicks, skips, saves, repeat plays).
- A higher relevance rate here does not automatically mean the same
  strategy would perform better against a real, full-scale catalog.

## 10. Feedback → next iteration

**Feedback (Supabase)**
→ **Aggregate relevance-rate per strategy** *(this doc, §8)*
→ **Once 50+ labeled votes exist: learned re-ranker activates** *(`utils/reranker.py`, see `05_final_report.md`)*
→ **Discuss findings with the team**
→ **Decide whether to keep, modify, or add a strategy**
→ **Update the PRD/solutioning docs**
→ **Run another comparison round**

Every resulting decision should be documented with the evidence behind it.
