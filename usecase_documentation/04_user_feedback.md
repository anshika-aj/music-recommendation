# 04 — User Feedback

## 1. Purpose

This document records feedback from evaluators who review the recommendation strategies in MUSICALLY.

Evaluators are team members/product or engineering stakeholders judging retrieval quality, not assumed end consumers.

Feedback is collected through the live Streamlit app and stored automatically in Supabase whenever an evaluator clicks 👍 or 👎.

> **Status:** live and collecting real feedback (not simulated). A first
> evaluation round across all 5 strategies exists (§5, §8); evaluator count
> and query variety are still low, so results are early signal, not a verdict.

## 2. Feedback fields

For every recommendation, the system records:

| Field | Meaning |
|---|---|
| `query_song` | Seed song selected by the evaluator ("Track — Artist") |
| `strategy` | Which strategy generated this recommendation. Ends in `+feedback` if feedback re-ranking was switched on when the vote was cast (e.g. `hybrid+feedback`) |
| `recommended_song` | Song being evaluated ("Track — Artist") |
| `vote` | `relevant` or `not_relevant` |
| `evaluator` | Auto-generated per-browser-session ID (see §3) |
| `created_at` | Timestamp, set automatically by Supabase |

The evaluator does **not** manually fill this table — every row above is written by the app.

## 3. How a vote becomes a record

**Evaluator picks a strategy from the sidebar** (and leaves feedback re-ranking on or off)
→ **Evaluator selects a seed song and searches**
→ **Recommendations appear, tagged with the active strategy**
→ **Evaluator clicks 👍 / 👎 on a result**
→ **`log_feedback()` inserts one row into the Supabase `feedback` table**
→ **Aggregate relevance rate (§8) is recalculated on next view**

**Repeated votes.** Raw rows are never deleted. When feedback is *used* (in
the aggregate table, the query-specific memory and the learned model), all rows
with the same `(query_song, strategy, recommended_song)` are collapsed into one
judgement by majority vote (a tie counts as `not_relevant`). Clicking the same
button many times therefore counts once. This was added after ~14 repeated 👍
on a single song during a live review inflated that strategy's numbers and
made the model overconfident.

**On the `evaluator` field specifically:** earlier in this project, every
row was logged with the same hardcoded value (`evaluator_01`) because of
a bug in a sidebar input — caught by checking the live Supabase table
directly. It's now fixed: on first load the app generates a random ID
(`evaluator_<8 hex chars>`) and stores it in the browser session. This is
**session-level**, not person-level — the same person voting from two
different tabs/devices appears as two evaluators. See §9.

## 4. Feedback storage

**Supabase** (hosted Postgres) — not a local CSV. Streamlit Community Cloud's
filesystem is ephemeral: a CSV would be silently wiped on every restart or
redeploy. Supabase persists independently of the app's lifecycle.

Table: `feedback`, columns as in §2, with Row-Level Security policies
controlling read/write access. Accessed from `utils/feedback.py` via the
`supabase-py` client. Free Supabase projects are paused after a period of
inactivity; if the app cannot reach the database, restore the project from the
Supabase dashboard.

## 5. Current snapshot

**First evaluation round — 80 votes.** One evaluator (the project author)
voted on **4 seed songs × all 5 strategies** (for example "Desi Kalakaar — Yo Yo
Honey Singh" and "Ab — The Local Train"), giving 80 rows. Per-strategy numbers
are in §8.

**Later votes — 110 rows in total at the time of the mentor review.** The
extra rows came from further test rounds (e.g. "Blank Space — Taylor Swift")
and from the mentor's live review, where the same song ("Faded — Alan Walker"
for the seed "Blinding Lights — The Weeknd") was voted 👍 about 14 times across
sessions. Those repeats are what exposed the problems fixed in the review
round, and why repeated votes now count once.

Not yet available: a shared fixed seed-song list, more than two people voting,
or votes cast with feedback re-ranking OFF vs ON in comparable numbers.

## 6. Questions for evaluators

### Understanding what "relevant" means

1. What makes a recommendation relevant — same genre, sound/mood, era, language, or something else?
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
| Oct 2026 | What do the match score and popularity on a card mean? | Match was a blended ranking score labelled like a similarity; popularity is Spotify's 0–100 score | Card now shows "sound match" = pure similarity; scores explained in the app |
| Oct 2026 | Why did ~13 👍 votes on one song change nothing? | Weight too small; model ignored the query; repeated votes counted as many | Query-specific memory added; repeated votes collapsed; see `03_solution.md` |
| Oct 2026 | Why do results contain several copies of the same song? | Dataset repeats songs under different track IDs; cleaning only removed repeated IDs | One row per (track, artist); query copies/covers excluded |

## 8. Aggregate evaluation

The app calculates, live, from Supabase:

**Relevance Rate = Relevant recommendations / Total evaluated recommendations**

First-round result (80 votes, 4 seed songs, one evaluator, counted **before**
repeated votes were collapsed — in this round each recommendation was voted once):

| Strategy | Relevant | Evaluated | Relevance rate |
|---|---:|---:|---:|
| `hybrid` | 13 | 13 | 100.0% |
| `genre_filtered` | 18 | 19 | 94.7% |
| `popularity_weighted` | 5 | 16 | 31.3% |
| `global_cosine` | 4 | 17 | 23.5% |
| `kmeans_restricted` | 1 | 15 | 6.7% |

Evaluated counts differ (13–19) because not every result was voted on.
Rows added after this round are not included; the in-app table now counts
unique judgements and also lists `<strategy>+feedback` rows separately.

## 9. Limitations

- Results are directional, not a production benchmark.
- Relevance judgments are subjective and evaluator-dependent. In the first
  round the evaluator's idea of "relevant" appears to track genre, language
  and artist — which structurally favours the two genre-based strategies.
- Only 4 seed songs and, in the first round, one evaluator.
- A rate of 13/13 on a small sample means "relevant every time so far", not
  "100% accurate".
- `evaluator` identifies a browser session, not a person.
- The dataset is a real but bounded subset of Spotify's catalog (~81k unique
  songs, 114 genres) — not the full catalog, and not production engagement
  data (clicks, skips, saves, repeat plays).
- A higher relevance rate here does not automatically mean the same
  strategy would perform better against a real, full-scale catalog.
- Once feedback re-ranking is ON, later results are shaped by earlier votes;
  those votes are tagged `+feedback` and must not be pooled with the plain
  strategy numbers.

## 10. Feedback → next iteration

**Feedback (Supabase)**
→ **Aggregate relevance-rate per strategy** *(§8)*
→ **Query-specific memory re-ranks results for the same seed song immediately**
→ **At 50+ unique labelled votes: learned re-ranker adds a general nudge** *(`utils/reranker.py`, see `05_final_report.md`)*
→ **Discuss findings with the team**
→ **Decide whether to keep, modify, or add a strategy**
→ **Update the PRD/solutioning docs**
→ **Run another comparison round**

Every resulting decision should be documented with the evidence behind it.
