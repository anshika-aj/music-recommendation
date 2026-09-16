# 02 — Product Requirements Document (PRD)

## 1. Product overview
MUSICALLY is a retrieval-strategy evaluation tool. On a controlled synthetic dataset (~80k songs with known audio features), it runs multiple recommendation strategies against the same queries — cluster-restricted KMeans, global cosine similarity, genre-filtered variants — so their relative performance can be compared before any strategy is applied to a real catalog.

## 2. Problem
No cheap, controlled way exists to compare recommendation strategies before committing to one at production scale.

## 3. Target user
A team building a music platform (product/eng), deciding what retrieval approach to invest in.

## 4. Use case
The goal isn't consumer music discovery — it's evaluating recommendation strategies on a controlled synthetic dataset before they'd be applied to a real catalog.

## 5. User story
"As a team building a music platform, I want to test how well different retrieval strategies surface relevant songs, so I can decide what to build at scale."

## 6. Functional requirements
- System can run a query song through multiple retrieval strategies (e.g. cluster-restricted KMeans, global similarity, genre-filtered)
- User can view/compare each strategy's top-N recommendations side by side for the same query
- User can mark a recommendation relevant/not relevant per strategy
- System stores per-strategy feedback for later comparison
- User can view aggregate results per strategy (e.g. relevance rate across test queries)

## 7. Non-functional requirements
- Reasonable response time when running multiple strategies per query
- Clear side-by-side comparison UI (not just a single ranked list)
- Reliable, repeatable results for the same query/strategy pair
- Maintainable code — easy to add a new strategy to compare

## 8. Success criteria
For the fixed test-query set, each strategy will receive evaluator relevance feedback. The system will calculate relevance rate per strategy, allowing the team to compare retrieval performance across the same queries.

Note: Results are directional because the evaluation uses a synthetic dataset and human relevance judgments rather than real user interaction data.
