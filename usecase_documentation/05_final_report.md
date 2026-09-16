# 05 — Final Report

## 1. Project

**MUSICALLY — Content-Based Music Recommendation System**

### Feature evaluated

**Recommendation Strategy Evaluation**

## 2. Executive Summary

MUSICALLY was originally built as a content-based music recommendation system using audio features.

The new feature extends it into a controlled environment for comparing multiple retrieval strategies against the same test queries.

The initial comparison includes:

- Cluster-restricted KMeans
- Global cosine similarity
- Genre-filtered retrieval

The evaluation uses a controlled synthetic dataset of approximately 80k songs.

The goal is not to claim production-level recommendation quality. The goal is to generate directional evidence about how different retrieval approaches behave before investing in a real catalog implementation.

> **Evaluation status:** Problem definition, PRD, and solutioning are complete. Final findings will be added after the comparison prototype is tested by evaluators and real feedback is collected.

## 3. Original System

**User selects song**
→ **Audio features**
→ **StandardScaler**
→ **KMeans**
→ **Cosine similarity**
→ **Ranked recommendations**
→ **Streamlit UI**

The original system returned a single recommendation list.

The limitation identified was that there was no structured way to compare this retrieval strategy with alternatives or record evaluator judgments.

## 4. Problem Identified

There are multiple reasonable retrieval approaches:

- Restrict search to the song's KMeans cluster.
- Search the complete dataset using cosine similarity.
- Apply genre constraints.
- Later investigate hybrid ranking.

The original system did not provide a controlled way to compare these alternatives.

## 5. New Use Case

MUSICALLY is being extended into a **retrieval-strategy evaluation tool**.

For the same seed song:

**One query**
→ **KMeans strategy**
→ **Global cosine strategy**
→ **Genre-filtered strategy**
→ **Side-by-side results**
→ **Evaluator feedback**
→ **Aggregate comparison**

The retrieval layer becomes modular so additional strategies can be added without redesigning the whole application.

## 6. Strategies Under Evaluation

| Strategy | Description | Status |
|---|---|---|
| Cluster-restricted KMeans | Retrieves candidates from the seed song's KMeans cluster | Baseline |
| Global cosine | Searches the full dataset using cosine similarity | Candidate |
| Genre-filtered | Applies genre filtering with similarity retrieval | In progress |
| Hybrid ranking | Combines multiple signals | Future candidate |

Global cosine is treated as a candidate for comparison, not a final production decision.

## 7. Evaluation Method

### Fixed test queries

Use a fixed set of approximately 5–10 seed songs.

The same queries are reused across evaluators so strategies receive the same inputs.

### Evaluator process

1. Run all configured strategies.
2. Display top-N recommendations side by side.
3. Evaluator marks each recommendation as:
   - Relevant 👍
   - Not relevant 👎
4. The application automatically records the feedback.
5. Aggregate relevance rates are calculated from stored feedback.

## 8. Automatic Feedback Collection

When an evaluator clicks 👍 or 👎, the Streamlit application creates a record containing:

```text
query_song
strategy
recommended_song
vote
evaluator
timestamp
```

Example:

```text
Believer
global_cosine
Song A
relevant
evaluator_01
2026-09-16 14:30:21
```

The evaluator does not manually enter these fields.

Initial storage:

```text
data/feedback.csv
```

or, if SQLite is selected:

```text
feedback.db
```

The aggregate view reads this stored data.

## 9. Evaluation Metric

**Relevance Rate**

```text
Relevance Rate =
Number of relevant recommendations
------------------------------------
Total recommendations evaluated
```

It can be calculated per strategy and across the fixed test-query set.

This is an evaluator-feedback metric, **not model accuracy**.

## 10. Results

### Current status

**Pending first evaluator round.**

No final strategy conclusion should be written until actual feedback has been collected.

### Overall results

| Strategy | Relevant | Evaluated | Relevance Rate |
|---|---:|---:|---:|
| Cluster-restricted KMeans | — | — | — |
| Global cosine | — | — | — |
| Genre-filtered | — | — | — |

### Per-query analysis

| Query | KMeans | Global Cosine | Genre-filtered | Observations |
|---|---:|---:|---:|---|
| | | | | |
| | | | | |
| | | | | |

Only actual evaluation results should be entered.

## 11. Qualitative Findings

After testing, record:

### What worked

- Recommendations consistently considered relevant.
- Useful strategy behaviour.
- Meaningful differences between strategies.

### What did not work

- Clearly irrelevant recommendations.
- Cases where a strategy excluded useful songs.
- Problems introduced by genre filtering.
- Noisy or ambiguous outputs.

### Unexpected findings

Record observations that differed from the initial expectation.

Findings should reflect the actual evaluator feedback.

## 12. Limitations

1. **Synthetic dataset:** It is not a live production music catalog.
2. **Human judgments:** Evaluators may disagree about relevance.
3. **No real user behaviour:** The evaluation does not measure clicks, skips, saves, listening duration, or repeat plays.
4. **Directional evidence:** Results inform what to investigate next but are not a production benchmark.
5. **Limited strategy set:** Only implemented and tested strategies can be compared.

## 13. Decision

This section will be completed after the first evaluation round.

The decision should consider:

- aggregate relevance rate,
- consistency across fixed queries,
- qualitative evaluator feedback,
- synthetic-data limitations,
- implementation complexity,
- requirements of the eventual real catalog.

Possible next actions:

- continue investigating a candidate strategy,
- modify an existing strategy,
- introduce a hybrid strategy,
- add another candidate and repeat the comparison.

The report should document the evidence and reasoning behind the selected next step.

## 14. Feedback Loop

**Problem**
→ **Requirements**
→ **PRD**
→ **Solutioning**
→ **Implementation**
→ **Evaluator Testing**
→ **Feedback**
→ **Analysis**
→ **Decision**
→ **Next PRD / iteration**

The purpose is to turn the project from a one-time recommendation demo into an iterative evaluation process.

## 15. Next Steps

### Immediate

1. Implement/refactor the strategy modules.
2. Add the side-by-side comparison UI.
3. Add automatic 👍/👎 feedback logging.
4. Create the fixed test-query set.
5. Run the first evaluator round.

### After testing

6. Calculate relevance rate per strategy.
7. Review qualitative feedback.
8. Discuss findings with the team.
9. Update solutioning based on evidence.
10. Document the next iteration.

## 16. Final Takeaway

MUSICALLY is being developed as a controlled environment for testing recommendation retrieval strategies before applying a chosen approach to a real catalog.

The value of the feature is the ability to:

**compare → collect feedback → measure → discuss → iterate**

using the same queries and a traceable feedback record.
