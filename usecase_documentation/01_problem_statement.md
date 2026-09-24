# 01 — Problem Statement

## Who is the user?
Not a music listener — a team building a music platform (product/eng team) that needs to decide which recommendation strategy to invest in before committing to one at scale.

## What problem are they facing?
There are multiple plausible retrieval strategies — full-catalogue cosine similarity, genre-filtered, KMeans cluster-restricted, popularity-weighted, and a hybrid of genre + cluster — and no cheap way to compare how well each one actually surfaces relevant songs before building any of them into a real product.

## What are they currently doing?
Picking a strategy based on intuition or convention (e.g. "KMeans is standard for this"), or building directly against a real catalog and finding out later that retrieval quality is poor — expensive to discover after the fact.

## Why is that inconvenient?
Testing strategies against a live, licensed catalog is costly and slow, and a bad retrieval choice discovered late means reworking a production system. There's no controlled, repeatable way to compare strategies side by side first.

## What are we trying to solve?
Build a controlled evaluation environment — using a public dataset of real Spotify tracks with real audio features (~81k unique tracks, 114 genres) — where different retrieval strategies can be run against the same queries and compared using real evaluator feedback, so a team can pick a strategy with evidence instead of guesswork before applying it to a real, licensed catalog.

## What assumptions are we making?
- This dataset can meaningfully differentiate strategies on *relative* performance (which one surfaces more relevant songs), even though it can't validate *absolute* relevance the way real listening/engagement data would.
- ~81k tracks across 114 genres is enough breadth to expose real trade-offs between strategies (e.g. where hard cluster/genre restriction excludes a relevant song a global search would have found).
- Results here are directional — informing what to build at scale — not a final production benchmark.

**Note:** an earlier draft of this document described the dataset as
"synthetic." That was incorrect — it's the public Kaggle "114k Spotify
Tracks" dataset, containing real audio-feature values for real, named
tracks (pulled via Spotify's own Audio Features API before that endpoint
was deprecated for new apps in November 2024). The actual limitation is
that it's a fixed *subset* of Spotify's catalog, not the full thing —
that's a licensing/scale limit, not a data-realism one.

**Note:** Evaluator feedback is also subjective, so the comparison should be interpreted as directional evidence rather than a definitive ranking of recommendation quality.
