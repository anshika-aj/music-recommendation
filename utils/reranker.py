"""
utils/reranker.py

Learned feedback re-ranker.

app.py's original feedback boost used a hand-guessed weight
(feedback_weight=0.05) applied to a song's raw historical relevance rate.
This module replaces that guess with an actual model, once there's enough
real feedback to train one honestly:

    - Below MIN_FEEDBACK_FOR_MODEL labeled votes, or if the votes logged so
      far are all "relevant" or all "not_relevant" (no real boundary to
      learn), get_learned_boost() returns (None, False) and app.py falls
      back to the original heuristic. A model trained on a handful of
      examples would just memorize noise, not learn anything real.
    - Once there's enough labeled data in both classes, a logistic
      regression is trained on (audio features -> relevant/not_relevant)
      and its predicted probability becomes the feedback boost. This
      learns which audio traits evaluators actually respond to, instead of
      everyone guessing a single weight.

Streamlit Community Cloud's filesystem is ephemeral (the same reason
feedback storage itself moved to Supabase — see utils/feedback.py), so the
model is never saved to disk. It's retrained in memory, cached for 5
minutes via st.cache_resource, and simply retrains from scratch next time
the cache expires or new feedback changes the row count.
"""

import numpy as np
import streamlit as st
from sklearn.linear_model import LogisticRegression

# Minimum labeled votes (across both relevant/not_relevant) before the
# learned re-ranker activates. Below this, a model would overfit to noise
# rather than learn anything real — see module docstring.
MIN_FEEDBACK_FOR_MODEL = 50


def _build_training_set(feedback_df, df, X_scaled):
    """
    Match each feedback row's recommended_song label ("Track — Artist")
    back to that song's scaled audio-feature vector in the dataset, so we
    can train on (features -> relevant/not_relevant).

    Feedback rows whose song label no longer matches anything in the
    current dataset (e.g. dataset was reloaded/changed) are skipped rather
    than erroring.
    """
    labels = df["track_name"] + " — " + df["artists"]
    label_to_pos = {}
    for pos, label in enumerate(labels):
        # First match wins for a duplicate label — rare in this dataset,
        # and not worth resolving ambiguously here.
        if label not in label_to_pos:
            label_to_pos[label] = pos

    rows, targets = [], []
    for _, fb in feedback_df.iterrows():
        pos = label_to_pos.get(fb["recommended_song"])
        if pos is None:
            continue
        rows.append(X_scaled[pos])
        targets.append(1 if fb["vote"] == "relevant" else 0)

    if not rows:
        return None, None
    return np.array(rows), np.array(targets)


@st.cache_resource(ttl=300)
def _train_reranker(_df, _X_scaled, _feedback_df, feedback_row_count):
    """
    Trains and caches the model. feedback_row_count is the actual cache
    key (a plain int, hashable); _df/_X_scaled/_feedback_df are excluded
    from hashing (leading underscore) since Streamlit can't hash a
    DataFrame/ndarray cheaply — the row count changing is what should
    trigger a retrain, not the object identity.
    """
    if feedback_row_count < MIN_FEEDBACK_FOR_MODEL:
        return None

    X, y = _build_training_set(_feedback_df, _df, _X_scaled)
    if X is None or len(np.unique(y)) < 2:
        # All labeled data is one class so far (all 👍 or all 👎) — no
        # boundary to learn yet, wait for more varied feedback.
        return None

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X, y)
    return model


def get_learned_boost(feedback_df, pool_scaled, df, X_scaled):
    """
    Returns (boost, used_model).

    boost      : predicted relevance probability (0..1) per pool song, or
                 None if the model isn't active yet.
    used_model : True if the learned model produced the boost; False means
                 the caller should fall back to the heuristic.
    """
    model = _train_reranker(df, X_scaled, feedback_df, len(feedback_df))
    if model is None:
        return None, False

    probs = model.predict_proba(pool_scaled)[:, 1]
    return probs, True
