# 05 — Final Report

## 1. Project

**MUSICALLY — Content-Based Music Recommendation System**

### Feature evaluated

**Recommendation Strategy Evaluation + Feedback-driven Re-ranking**

## 2. Executive Summary

MUSICALLY was originally a content-based music recommender returning a
single ranked list per query. It has been extended into (a) a
5-strategy comparison tool, and (b) a feedback pipeline that reports on
strategy performance and also changes future rankings.

The dataset is the public Kaggle "114k Spotify Tracks" dataset — real
audio-feature values for real, named tracks (~81k unique songs after
keeping one copy per track/artist, 114 genres), not synthetic data. It's a
bounded subset of Spotify's catalog, not the full thing.

**First evidence (80 votes, 4 seed songs, one evaluator):** the two
strategies that restrict candidates to the query song's genre
(`hybrid` 13/13, `genre_filtered` 18/19) were judged relevant far more often
than the audio-only ones (`popularity_weighted` 5/16, `global_cosine` 4/17,
`kmeans_restricted` 1/15). This is directional, not conclusive (§12).

**Review round (Oct 2026):** a mentor review of the live app found duplicate
songs, feedback buttons with no visible effect, an unexplained match score, and
outdated documents. Each was traced to a root cause and fixed — see §10 and
`03_solution.md`.

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
→ **Score = similarity + popularity + feedback terms** *(formula in `03_solution.md`)*
→ **Query's own copies removed, each song shown once, artist cap**
→ **Top-N cards: "N% sound match", popularity, 👍/👎**
→ **Vote logged to Supabase, tagged with strategy (+`+feedback` if re-ranking was on) and session evaluator ID**
→ **Aggregate relevance-rate view; query-specific memory; learned re-ranker**

## 5. Strategies Under Evaluation

| Strategy | Candidate pool | Status |
|---|---|---|
| `global_cosine` | Full dataset | Implemented |
| `genre_filtered` | Same `track_genre` as the query song | Implemented |
| `kmeans_restricted` | Same KMeans `cluster` as the query song | Implemented |
| `popularity_weighted` | Full dataset, popularity weighted much higher in scoring | Implemented |
| `hybrid` | Same genre **and** same cluster | Implemented |

## 6. Evaluation Method

**Strategy selection:** an evaluator picks one of the 5 strategies per search
from a sidebar dropdown; every vote is tagged with it.

**Evaluator process:**
1. Pick a strategy and a seed song.
2. View the top-N recommendations.
3. Mark each as relevant 👍 or not relevant 👎.
4. The app records the vote automatically (query, strategy, song, vote,
   session evaluator ID, timestamp) to Supabase.
5. Aggregate relevance rates recompute live.

**Clean vs feedback-influenced runs:** for a strategy comparison, feedback
re-ranking should be OFF, so the strategy alone decides the list. Votes cast
with it ON are stored as `<strategy>+feedback` and kept out of the plain rates.
The first 80 votes were cast before query-specific feedback existed, so they
are effectively clean.

**Fixed test queries:** the first round used 4 seed songs chosen by the
evaluator. A shared list of 5–10 fixed seeds is still a next step (§15).

## 7. Automatic Feedback Collection

Schema (Supabase `feedback` table):
```text
query_song, strategy, recommended_song, vote, evaluator, created_at
```
Written by `log_feedback()` in `utils/feedback.py` on every 👍/👎 click. See
`04_user_feedback.md` for schema notes, the evaluator-ID bug/fix history and
how repeated votes are counted.

## 8. Evaluation Metric

**Relevance Rate = relevant recommendations / total evaluated**, computed per
strategy over *unique judgements* (repeated votes on the same query + strategy
+ song count once). It is an evaluator-feedback metric, not model accuracy.

## 9. Results

### First evaluation round — 80 votes, 4 seed songs, one evaluator

| Strategy | Relevant | Evaluated | Relevance Rate |
|---|---:|---:|---:|
| `hybrid` | 13 | 13 | 100.0% |
| `genre_filtered` | 18 | 19 | 94.7% |
| `popularity_weighted` | 5 | 16 | 31.3% |
| `global_cosine` | 4 | 17 | 23.5% |
| `kmeans_restricted` | 1 | 15 | 6.7% |

### What it suggests

- **Genre restriction is what made results feel relevant.** `hybrid` and
  `genre_filtered` are almost identical; adding the cluster condition on top of
  genre changed little.
- **Clusters on audio features alone are a poor gate.** `kmeans_restricted` was
  the worst. This agrees with the earlier observation that a cluster is a rough
  audio neighbourhood, not a genre (README, Model Fix #2).
- **Popularity weighting alone did not help**: 5/16 vs 4/17 for `global_cosine`
  is within noise and should not be presented as a difference.
- **Relevant is not the same as good.** The tight pools of `hybrid` tend to
  return songs from the same few artists/style (relevant but narrow); a
  production choice would weigh relevance against diversity and novelty.

### Reading these numbers honestly

One evaluator, 4 seed songs, uneven votes per strategy (13–19), and an
evaluator whose notion of "relevant" seems to follow genre, language and
artist — which favours genre-based pools by construction. "13/13" means
"relevant every time so far", not "100% accurate". Treat the table as the first
signal to confirm with more evaluators and a fixed seed list.

Votes added after this round are not in the table (some are repeats and some
were cast with feedback re-ranking on); the in-app table now shows unique
judgements and separates `+feedback` rows.

## 10. Feedback Use — Methodology, Status, and What the Review Found

Three mechanisms use the feedback:

1. **Aggregate relevance rate** (above) — for comparing strategies.
2. **Query-specific memory** — for the *same seed song*, results voted 👍
   move up and results voted 👎 move down (`(2·relevant − n)/(n + 1)`, weight
   0.10). This is the visible effect of the 👍/👎 buttons.
3. **Learned re-ranker** (`utils/reranker.py`) — logistic regression on the
   10 audio features of the recommended song → relevant / not relevant, active
   at 50+ unique labelled votes with both classes present; weight 0.05. Below
   that threshold a per-song relevance rate is used. The live app displayed
   "Learned re-ranker active — trained on 110 votes" when checked; the
   threshold is now counted on unique judgements, and the caption says so.

**What the mentor review found, and the fixes**

| Concern | Where the system lagged | Fix |
|---|---|---|
| Duplicates | Dataset stores a song once per release; cleaning removed repeated track IDs only (~8,400 songs still repeated); the query's own copies could be recommended | One row per (track, artist); query copies/covers excluded; near-identical titles shown once |
| Feedback had no visible effect | 5% weight on a ~1% score spread; model ignored the query and replaced per-song history; repeated votes counted as many | Query-specific memory (0.10), repeated votes collapse, model kept as a small extra |
| Match score unclear | Card showed the blended ranking score, labelled "match"; popularity unexplained | Card shows "N% sound match" (pure similarity); popularity labelled; formula printed in the app |
| Outdated documents | Docs, README and live app disagreed (catalogue size, vote counts, re-ranker status, results) | All documents rewritten against the current code and data |

**Known limitation of the learned re-ranker:** it learns general audio taste
from the recommended song only, and does not know which query it was
recommended for. With 4–5 seed songs it will mostly reflect those seeds'
styles. This is why its weight stays small and why a query-aware version is
listed under next steps. Which audio features it weights most has not been
inspected yet, so no claim about that is made here.

## 11. Qualitative Findings

Observed in the first round (seed "Desi Kalakaar — Yo Yo Honey Singh"):
- `hybrid` returned Punjabi hip-hop/pop tracks (e.g. Sidhu Moose Wala, Jordan
  Sandhu, Dilpreet Dhillon) — all marked relevant.
- `popularity_weighted` returned very popular Spanish-language and global pop
  tracks (e.g. Maluma, Bad Bunny, Shakira) — mostly not relevant; "Starboy" was
  the exception marked relevant.
- `kmeans_restricted` returned a track from an unrelated genre and language
  (Anne-Marie) — not relevant.

Still to record from a wider round: where evaluators disagreed, and whether
genre/cluster restriction traded relevance for narrowness.

## 12. Limitations

1. **Bounded dataset:** ~81k unique real songs across 114 genres — real audio
   features, but not the full Spotify catalog, and not licensed for production use.
2. **Human judgment:** evaluators may disagree about relevance, and the
   `evaluator` field identifies a browser session, not a verified person.
3. **No real user behaviour:** votes are explicit judgements, not clicks,
   skips, saves, or repeat plays.
4. **Directional evidence:** informs what to investigate next, not a
   production benchmark.
5. **Small sample:** 80 votes, 4 seed songs, one evaluator in the first round.
6. **Scale:** similarity is computed brute-force against the pool on every
   search — fine at ~81k songs. A far larger catalogue would need an
   approximate nearest-neighbour index (e.g. FAISS or pgvector).

## 13. Decision

**Provisional** — to be confirmed with more evaluators and a fixed seed list:

- Build genre-aware retrieval first; adding a cluster condition on top of
  genre was not a measurable gain here.
- Do not use an audio-only cluster as a retrieval gate on its own.
- Do not claim popularity weighting helps; the data shows no difference.
- Keep feedback in the loop (query-specific memory) but evaluate strategies
  with feedback re-ranking OFF, and compare `<strategy>` with
  `<strategy>+feedback` to test whether feedback actually raises relevance.

## 14. Feedback Loop

**Problem → Requirements → PRD → Solutioning → Implementation → Evaluator
Testing → Feedback → Analysis → Mentor review → Fixes → Next iteration**

## 15. Next Steps

### Immediate
1. Agree on 5–10 fixed seed songs across different genres and languages
   (not only Punjabi/Hindi), and get 2–3 more evaluators to vote on all 5
   strategies with feedback re-ranking OFF.
2. Re-run the aggregate table (it now counts unique judgements) and update §9.
3. Run a second pass with feedback re-ranking ON and compare
   `<strategy>` vs `<strategy>+feedback`.

### After that
4. Make the learned re-ranker query-aware (input: recommended song's features
   *and* its difference from the query song).
5. Inspect which audio features the model weights most and record it here.
6. Decide: keep, tune, or add a strategy; document the next iteration.

## 16. Final Takeaway

MUSICALLY is a working, live environment for comparing 5 retrieval strategies
with real evaluator feedback. The first round points to genre-aware retrieval
as the better foundation and against audio-only cluster gating, and the review
round made the system trustworthy enough to repeat that test: songs appear
once, scores are explained, and a 👍 or 👎 visibly changes the next result. The
honest state is early evidence from few evaluators; the next milestone is more
evaluators on a shared seed list.
