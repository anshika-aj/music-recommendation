# 05 — Final Report

## 1. Project

**MUSICALLY — Content-Based Music Recommendation System**

### Feature evaluated

**Recommendation Strategy Evaluation + Learned Feedback Re-ranking**

## 2. Executive Summary

MUSICALLY was originally a content-based music recommender returning a
single ranked list per query. It has been extended into (a) a
5-strategy comparison tool, and (b) a feedback pipeline that both reports
on strategy performance and, once there's enough data, actively improves
future rankings.

The dataset is the public Kaggle "114k Spotify Tracks" dataset — real
audio-feature values for real, named tracks (~81k unique after
de-duplication, 114 genres), not synthetic data. It's a bounded subset of
Spotify's catalog, not the full thing.

> **Status as of this report:** all 5 strategies are implemented and live
> in the deployed app. Feedback collection is live and Supabase-backed.
> Real vote count is still small and concentrated on one strategy/query —
> not yet enough for a meaningful cross-strategy comparison or for the
> learned re-ranker to activate. This report states that plainly rather
> than filling in numbers that don't exist yet.

## 3. Original System

**User selects song**
→ **Audio features + StandardScaler**
→ **Cosine similarity (full dataset; KMeans for exploratory analysis only)**
→ **Ranked recommendations**
→ **Streamlit UI**

Limitation identified: no structured way to compare this approach against
alternatives, and no mechanism to record evaluator judgment at all.

## 4. Current System

**User selects a song and a strategy**
→ **`build_pool()` selects the candidate pool for that strategy**
→ **Cosine similarity within that pool**
→ **Score = similarity + popularity + feedback boost**
→ **Top-N shown, with 👍/👎 per result**
→ **Vote logged to Supabase, tagged with strategy + session evaluator ID**
→ **Aggregate relevance-rate view (live)**
→ **Learned re-ranker (activates automatically past a data threshold)**

## 5. Strategies Under Evaluation

| Strategy | Candidate pool | Status |
|---|---|---|
| `global_cosine` | Full dataset | Implemented |
| `genre_filtered` | Same `track_genre` as the query song | Implemented |
| `kmeans_restricted` | Same KMeans `cluster` as the query song | Implemented |
| `popularity_weighted` | Full dataset, popularity weighted much higher in scoring | Implemented |
| `hybrid` | Same genre **and** same cluster | Implemented |

All 5 are live in the deployed app now — none are "future candidates."

## 6. Evaluation Method

**Strategy selection:** an evaluator explicitly picks one of the 5
strategies per search from a sidebar dropdown; every vote is tagged with
whichever strategy was active when it was cast.

**Evaluator process:**
1. Pick a strategy and a seed song.
2. View the top-N recommendations for that strategy.
3. Mark each as relevant 👍 or not relevant 👎.
4. The app records the vote automatically (query, strategy, song, vote,
   session evaluator ID, timestamp) to Supabase.
5. Aggregate relevance rates recompute live from stored feedback.

**Fixed test queries:** not yet formally enforced — evaluators have so far
searched arbitrary songs. Recommended next step: agree on 5–10 fixed seed
songs so results across evaluators and strategies are apples-to-apples
(see §15).

## 7. Automatic Feedback Collection

Schema (Supabase `feedback` table):
```text
query_song, strategy, recommended_song, vote, evaluator, created_at
```
The evaluator never enters these fields manually — `log_feedback()` in
`utils/feedback.py` writes them on every 👍/👎 click. See
`04_user_feedback.md` for the full schema notes and the evaluator-ID
bug/fix history.

## 8. Evaluation Metric

**Relevance Rate = relevant recommendations / total evaluated**, computed
per strategy via `relevance_rate()` — a live query against Supabase, not
a static number. This is an evaluator-feedback metric, not model accuracy.

## 9. Results

### Current status: pending a proper evaluator round

Real votes exist but are concentrated on a single strategy/query so far —
not yet a valid basis for a cross-strategy conclusion. No strategy
ranking should be claimed until votes are spread across all 5 strategies
and multiple queries.

### Overall results

| Strategy | Relevant | Evaluated | Relevance Rate |
|---|---:|---:|---:|
| `global_cosine` | — | — | — |
| `genre_filtered` | — | — | — |
| `kmeans_restricted` | — | — | — |
| `popularity_weighted` | — | — | — |
| `hybrid` | — | — | — |

*(Populate from `relevance_rate()`'s live output once evaluator testing
covers all 5 strategies — see §15 for the concrete next step.)*

## 10. Learned Re-ranker — Methodology and Status

The original feedback boost applied a hand-picked weight
(`feedback_weight=0.05`) to a song's historical relevance rate, with no
data behind the number. `utils/reranker.py` replaces this with a proper
model, gated behind a real-data threshold so it can't be presented as
"learned" when it's actually just overfit to a handful of examples:

- **Below 50 labeled votes, or if all votes so far are one-sided** (all
  👍 or all 👎): the original heuristic remains active. This is the
  current state.
- **At 50+ labeled votes with both classes present:** a logistic
  regression trains on `(audio features → relevant/not_relevant)` from
  real Supabase feedback, and its predicted probability becomes the
  boost — weights the data actually justifies, not a guess.
- The app shows, live, which mode is active (`🧠 Learned re-ranker
  active` vs `📊 Using heuristic feedback boost — N/50 votes`), so this
  is always verifiable rather than asserted.
- Once the threshold is crossed, this section should be updated with
  which audio features the model weighted most heavily (from the trained
  model's coefficients) — a genuine finding, not available yet.

## 11. Qualitative Findings

Not yet populated — genuinely pending a real evaluator round across all 5
strategies. Will record, once available: which recommendations evaluators
consistently agreed were relevant, which strategy produced surprising or
clearly wrong results, and whether genre/cluster restriction visibly
traded relevance for narrowness.

## 12. Limitations

1. **Bounded dataset:** ~81k real tracks across 114 genres — real audio
   features, but not the full Spotify catalog, and not licensed for
   production use.
2. **Human judgment:** evaluators may disagree about relevance, and
   `evaluator` currently identifies a browser session, not a verified
   person (see `04_user_feedback.md` §9).
3. **No real user behavior:** votes are explicit judgments, not clicks,
   skips, saves, or repeat plays.
4. **Directional evidence:** informs what to investigate next, not a
   production benchmark.
5. **Small current sample:** not yet enough spread across strategies/
   queries for the results in §9 to mean anything — stated plainly rather
   than papered over.

## 13. Decision

Not yet reached — genuinely pending real evaluator data across all 5
strategies (§9) and, separately, the learned re-ranker crossing its
50-vote threshold (§10). Once both exist, this section should weigh:
aggregate relevance rate, consistency across fixed queries, qualitative
evaluator feedback, dataset-scope limitations, and what the learned
re-ranker's feature weights revealed.

## 14. Feedback Loop

**Problem → Requirements → PRD → Solutioning → Implementation → Evaluator
Testing → Feedback → Analysis → Decision → Next iteration**

This closes at "Decision" only once real, spread-out feedback exists —
not before.

## 15. Next Steps

### Immediate
1. Get more real evaluators voting, explicitly across all 5 strategies
   (not just `global_cosine`) and a shared set of query songs.
2. Formalize a fixed 5–10 seed-song test set so results are comparable.
3. Once votes are spread out: populate §9's results table for real.

### Once 50+ labeled votes exist
4. Confirm the learned re-ranker activated (check the UI status caption).
5. Record which audio features it weighted most heavily.
6. Compare recommendations before/after the re-ranker activated.

### After that
7. Discuss findings with the team.
8. Decide: keep the current strategy set, tune one, or add a new
   candidate and repeat the comparison.
9. Document the next iteration.

## 16. Final Takeaway

MUSICALLY is a working, live environment for comparing 5 retrieval
strategies using real evaluator feedback, with a feedback pipeline that
does two real jobs: reporting (the aggregate relevance table) and
learning (the re-ranker, once enough data exists). The honest current
state is: built and deployed, evaluator testing still early — the next
concrete milestone is simply getting more real votes spread across
strategies and queries.
