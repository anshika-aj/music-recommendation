import pandas as pd
from pathlib import Path
from datetime import datetime

FEEDBACK_PATH = Path("data/feedback.csv")
FEEDBACK_COLUMNS = ["query_song", "strategy", "recommended_song", "vote", "evaluator", "timestamp"]


def _ensure_file():
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_PATH.exists():
        pd.DataFrame(columns=FEEDBACK_COLUMNS).to_csv(FEEDBACK_PATH, index=False)


def log_feedback(query_song: str, strategy: str, recommended_song: str, vote: str, evaluator: str):
    _ensure_file()
    row = {
        "query_song": query_song,
        "strategy": strategy,
        "recommended_song": recommended_song,
        "vote": vote,
        "evaluator": evaluator,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pd.DataFrame([row]).to_csv(FEEDBACK_PATH, mode="a", header=False, index=False)


def load_feedback() -> pd.DataFrame:
    _ensure_file()
    return pd.read_csv(FEEDBACK_PATH)


def relevance_rate(df: pd.DataFrame = None) -> pd.DataFrame:
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
