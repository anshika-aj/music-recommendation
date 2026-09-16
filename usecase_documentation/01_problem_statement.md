# 01 — Problem Statement

## Who is the user?
Not a music listener — a team building a music platform (product/eng team) that needs to decide which recommendation strategy to invest in before committing to one at scale.

## What problem are they facing?
There are multiple plausible retrieval strategies (cluster-restricted KMeans, global cosine similarity, hybrid ranking, genre-filtered variants) and no cheap way to compare how well each one actually surfaces relevant songs before building any of them into a real product.

## What are they currently doing?
Picking a strategy based on intuition or convention (e.g. "KMeans is standard for this"), or building directly against a real catalog and finding out later that retrieval quality is poor — expensive to discover after the fact.

## Why is that inconvenient?
Testing strategies against a live, licensed catalog is costly and slow, and a bad retrieval choice discovered late means reworking a production system. There's no controlled, repeatable way to compare strategies side by side first.

## What are we trying to solve?
Build a controlled evaluation environment — a synthetic ~80k song dataset with known audio features — where different retrieval strategies can be run against the same queries and compared, so a team can pick a strategy with evidence instead of guesswork before applying it to a real catalog.

## What assumptions are we making?
- A synthetic dataset can meaningfully differentiate strategies on *relative* performance (which one surfaces more relevant songs), even if it can't validate *absolute* relevance the way real listening data would.
- 80k songs is enough breadth to expose the trade-offs between strategies (e.g. where hard clustering excludes relevant songs).
- Results here are directional — informing what to build at scale — not a final production benchmark.


NOTE- Evaluator feedback is also subjective, so the comparison should be interpreted as directional evidence rather than a definitive ranking of recommendation quality.