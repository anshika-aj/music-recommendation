# 02 — Product Requirements Document (PRD)

## 1. Product overview
MUSICALLY is a retrieval-strategy evaluation tool. On a public dataset of ~81k real Spotify tracks with real audio features, it runs 5 recommendation strategies against the same queries — global cosine similarity, genre-filtered, KMeans cluster-restricted, popularity-weighted, and a genre+cluster hybrid — so their relative performance can be compared before any strategy is applied to a real, licensed catalog.

## 2. Problem
No cheap, controlled way exists to compare recommendation strategies before committing to one at production scale.

## 3. Target user
A team building a music platform (product/eng), deciding what retrieval approach to invest in.

## 4. Use case
The goal isn't consumer music discovery — it's evaluating recommendation strategies on a controlled, real-track dataset before they'd be applied to a real, licensed catalog at scale.

## 5. User story
"As a team building a music platform, I want to test how well different retrieval strategies surface relevant songs, so I can decide what to build at scale."

## 6. Functional requirements
- System can run a query song through 5 retrieval strategies: `global_cosine`, `genre_filtered`, `kmeans_restricted`, `popularity_weighted`, `hybrid` — **status: implemented**
- User can select which strategy to search with, and results are tagged with that strategy — **status: implemented**
- User can mark a recommendation relevant/not relevant per strategy — **status: implemented**
- System stores per-strategy feedback for later comparison, persisted across app restarts — **status: implemented (Supabase)**
- Each evaluator's votes are distinguishable from each other's — **status: implemented (auto-generated per-session ID; see `03_solution.md` for the bug this replaced)**
- User can view aggregate results per strategy (relevance rate across test queries) — **status: implemented, awaiting enough real votes to be meaningful**
- Feedback is used to actually improve future rankings, not just displayed — **status: implemented as a two-tier system — a heuristic active now, a learned model that activates once 50+ labeled votes exist (see `05_final_report.md`)**

## 7. Non-functional requirements
- Reasonable response time when running a strategy per query (single strategy per search now, not all 5 simultaneously — simpler and faster than the original side-by-side-columns plan, see `03_solution.md`)
- Clear indication of which strategy produced the results being viewed
- Reliable, repeatable results for the same query/strategy pair
- Maintainable code — adding a 6th strategy should be a small, local change

## 8. Success criteria
For a fixed set of test queries, each strategy will receive evaluator relevance feedback. The system calculates relevance rate per strategy, letting the team compare retrieval performance across the same queries.

Note: results are directional — this uses a real-track dataset that is nonetheless a bounded subset of Spotify's catalog, and relies on human relevance judgments rather than production engagement data (clicks, skips, saves, repeat plays).
