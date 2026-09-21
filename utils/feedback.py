"""
utils/feedback.py

Feedback storage backed by Supabase (hosted Postgres), so votes persist
across Streamlit Community Cloud restarts/redeploys — a local CSV or
SQLite file does not survive those.

Public API is unchanged from the CSV version (log_feedback, load_feedback,
relevance_rate), so app.py does not need any changes for this swap.

Requires:
    - a Supabase project with a `feedback` table (see the CREATE TABLE
      statement provided alongside this file)
    - SUPABASE_URL and SUPABASE_KEY set in .streamlit/secrets.toml
      (locally) and in the app's Secrets panel on Streamlit Cloud
    - `pip install supabase` (also add to requirements.txt)
"""

import streamlit as st
import pandas as pd
from supabase import create_client

_supabase = None


def _client():
    """Lazily create the Supabase client so importing this module doesn't
    require secrets to be present (e.g. during local linting/tests)."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return _supabase


def log_feedback(query_song: str, strategy: str, recommended_song: str, vote: str, evaluator: str):
    """
    Insert one feedback record. vote must be "relevant" or "not_relevant"
    (matches docs/04_user_feedback.md and the table's CHECK constraint).
    """
    _client().table("feedback").insert({
        "query_song": query_song,
        "strategy": strategy,
        "recommended_song": recommended_song,
        "vote": vote,
        "evaluator": evaluator,
    }).execute()


def load_feedback() -> pd.DataFrame:
    """Return all logged feedback as a DataFrame."""
    response = _client().table("feedback").select("*").execute()
    if not response.data:
        return pd.DataFrame(columns=[
            "id", "query_song", "strategy", "recommended_song",
            "vote", "evaluator", "created_at",
        ])
    return pd.DataFrame(response.data)


def relevance_rate(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Relevance Rate = relevant / evaluated, per strategy.
    Same aggregation as the CSV version — docs/04_user_feedback.md Section 8.
    """
    if df is None:
        df = load_feedback()
    if df.empty:
        return pd.DataFrame(columns=["strategy", "relevant", "evaluated", "relevance_rate"])

    grouped = df.groupby("strategy")["vote"].agg(
        relevant=lambda x: (x == "relevant").sum(),
        evaluated="count",
    ).reset_index()
    grouped["relevance_rate"] = (grouped["relevant"] / grouped["evaluated"]).round(3)
    return grouped


def song_relevance_stats() -> pd.DataFrame:
    """
    Per-song relevance rate across all feedback, keyed by recommended_song
    ("Track — Artist", matching the label format used when logging).
    Used by the recommender to re-rank based on historical feedback —
    see get_feedback_boost() usage in app.py's recommend().
    """
    df = load_feedback()
    if df.empty:
        return pd.DataFrame(columns=["recommended_song", "relevant", "evaluated", "relevance_rate"])

    grouped = df.groupby("recommended_song")["vote"].agg(
        relevant=lambda x: (x == "relevant").sum(),
        evaluated="count",
    ).reset_index()
    grouped["relevance_rate"] = (grouped["relevant"] / grouped["evaluated"]).round(3)
    return grouped
