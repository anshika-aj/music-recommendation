import streamlit as st
import pandas as pd
import numpy as np
import joblib
from spotify_api import get_album_cover
from sklearn.metrics.pairwise import cosine_similarity
from utils.feedback import log_feedback, load_feedback, relevance_rate
from utils.reranker import get_learned_boost, MIN_FEEDBACK_FOR_MODEL
import uuid

if "evaluator_id" not in st.session_state:
    st.session_state.evaluator_id = f"evaluator_{uuid.uuid4().hex[:8]}"

# Retrieval strategies available for comparison (docs/03_solution.md).
# key -> (display label, short description shown under the picker)
STRATEGIES = {
    "global_cosine": (
        "Global Cosine Similarity",
        "Full-catalogue nearest neighbour on audio features — no filtering.",
    ),
    "genre_filtered": (
        "Genre-Filtered Cosine",
        "Cosine similarity restricted to songs in the query song's own genre.",
    ),
    "kmeans_restricted": (
        "KMeans Cluster-Restricted",
        "Cosine similarity restricted to songs in the query song's KMeans sound cluster.",
    ),
    "popularity_weighted": (
        "Popularity-Weighted",
        "Global similarity, but popularity counts for much more in the final ranking.",
    ),
    "hybrid": (
        "Hybrid (Genre + Cluster)",
        "Cosine similarity restricted to songs matching BOTH genre and cluster — the tightest pool.",
    ),
}

st.set_page_config(
    page_title="Music recommender: MUSICALLY",
    page_icon="🎵",
    layout="wide"
)

df = pd.read_csv("dataset/spotify_clustered_dataset.csv")
scaler = joblib.load("models/scaler.joblib")
kmeans = joblib.load("models/kmeans.joblib")  # kept for EDA/cluster count metric only

DEFAULT_IMAGE = "https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_CMYK_Green.png"

# ---------------------------------------------------------------------------
# Design tokens
#   bg        #0B0F0D  near-black, faint green undertone
#   surface   #141B17  elevated card surface
#   line      #223028  hairline borders
#   accent    #29D398  emerald — the app's one bright color
#   highlight #FFC857  warm amber — used only for the match badge
#   text      #F5F7F5  soft off-white
#   muted     #93A29B  sage grey
# ---------------------------------------------------------------------------

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

:root{
    --bg:#0B0F0D;
    --surface:#141B17;
    --line:#223028;
    --accent:#29D398;
    --accent-dim:#1B8F68;
    --highlight:#FFC857;
    --text:#F5F7F5;
    --muted:#93A29B;
}

html, body, [class*="css"]{
    font-family:'Inter', sans-serif;
}

h1,h2,h3,h4{
    font-family:'Sora', sans-serif;
}

.stApp{
    background:var(--bg);
    color:var(--text);
}

section[data-testid="stSidebar"]{
    background:var(--surface);
    border-right:1px solid var(--line);
}

.block-container{
    padding-top:2rem;
    max-width:1200px;
}

.hero{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:24px;
    padding:36px 40px;
    margin-bottom:28px;
    border-radius:20px;
    background:linear-gradient(120deg, #0E4A38 0%, #0B0F0D 75%);
    border:1px solid var(--line);
}

.hero-title{
    font-size:34px;
    font-weight:800;
    color:var(--text);
    margin:0 0 6px 0;
}

.hero-sub{
    font-size:15px;
    color:var(--muted);
    margin:0;
    max-width:480px;
}

.hero-mark{
    font-size:44px;
    line-height:1;
}

.stat-strip{
    display:flex;
    align-items:baseline;
    gap:36px;
    padding:18px 4px 28px 4px;
    border-bottom:1px solid var(--line);
    margin-bottom:28px;
    flex-wrap:wrap;
}

.stat-lead .stat-num{
    font-size:36px;
    font-weight:800;
    color:var(--accent);
    font-family:'Sora', sans-serif;
}

.stat-lead .stat-label{
    font-size:13px;
    color:var(--muted);
}

.stat-minor{
    display:flex;
    flex-direction:column;
}

.stat-minor .stat-num{
    font-size:20px;
    font-weight:600;
    color:var(--text);
    font-family:'Sora', sans-serif;
}

.stat-minor .stat-label{
    font-size:12px;
    color:var(--muted);
}

.sidebar-title{
    font-family:'Sora', sans-serif;
    font-size:20px;
    font-weight:700;
    color:var(--text);
    margin-bottom:2px;
}

.sidebar-sub{
    font-size:12px;
    color:var(--accent);
    margin-bottom:18px;
}

.chip-row{
    display:flex;
    flex-wrap:wrap;
    gap:6px;
    margin-top:6px;
}

.chip{
    font-size:11px;
    color:var(--text);
    background:rgba(41,211,152,0.12);
    border:1px solid rgba(41,211,152,0.35);
    padding:5px 10px;
    border-radius:20px;
}

.rec-grid{
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));
    gap:22px;
    margin-top:6px;
}

.poster-card{
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:16px;
    overflow:hidden;
    transition:transform .15s ease, border-color .15s ease;
}

.poster-card:hover{
    transform:translateY(-4px);
    border-color:var(--accent-dim);
}

.poster-image{
    position:relative;
    width:100%;
    aspect-ratio:1/1;
    background-size:cover;
    background-position:center;
    display:flex;
    align-items:flex-end;
}

.poster-badge{
    position:absolute;
    top:10px;
    right:10px;
    background:var(--highlight);
    color:#241A00;
    font-size:12px;
    font-weight:700;
    padding:4px 9px;
    border-radius:20px;
}

.poster-scrim{
    width:100%;
    padding:34px 14px 12px 14px;
    background:linear-gradient(180deg, rgba(11,15,13,0) 0%, rgba(11,15,13,0.92) 78%);
}

.poster-scrim h4{
    margin:0;
    font-size:15px;
    color:#fff;
    line-height:1.25;
}

.poster-scrim p{
    margin:2px 0 0 0;
    font-size:12.5px;
    color:rgba(255,255,255,0.75);
}

.poster-meta{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:10px 14px 14px 14px;
}

.genre-chip{
    font-size:11px;
    color:var(--accent);
    background:rgba(41,211,152,0.10);
    padding:3px 9px;
    border-radius:20px;
}

.pop-meta{
    font-size:11.5px;
    color:var(--muted);
}
"""

# Collapse to one line with no newlines/indentation at all — Streamlit's
# markdown renderer can misparse a multi-line <style> block (blank lines or
# leading whitespace get read as markdown, not CSS). A single unbroken line
# leaves nothing for it to misinterpret.
st.markdown(
    "<style>" + " ".join(_CSS.split()) + "</style>",
    unsafe_allow_html=True
)

feature_columns = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms"
]

# ---------- Hero ----------
st.markdown(f"""
<div class="hero">
  <div>
    <p class="hero-title">MUSICALLY</p>
    <p class="hero-sub">Find your next favourite song by sound, not just genre — matched on tempo, energy, mood and ten other audio traits.</p>
  </div>
  <div class="hero-mark">🎧</div>
</div>
""", unsafe_allow_html=True)

# ---------- Stat strip ----------
st.markdown(f"""
<div class="stat-strip">
  <div class="stat-lead">
    <div class="stat-num">{len(df):,}</div>
    <div class="stat-label">songs in the library</div>
  </div>
  <div class="stat-minor">
    <div class="stat-num">{df.track_genre.nunique()}</div>
    <div class="stat-label">genres</div>
  </div>
  <div class="stat-minor">
    <div class="stat-num">{df.cluster.nunique()}</div>
    <div class="stat-label">sound clusters</div>
  </div>
  <div class="stat-minor">
    <div class="stat-num">{len(feature_columns)}</div>
    <div class="stat-label">audio features</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.markdown("""
<div class="sidebar-title">🎵 MUSICALLY</div>
<div class="sidebar-sub">Content-based recommendation</div>
""", unsafe_allow_html=True)

st.sidebar.metric("Songs", f"{len(df):,}")
st.sidebar.metric("Genres", df.track_genre.nunique())
st.sidebar.metric("Clusters", df.cluster.nunique())

st.sidebar.divider()

st.sidebar.markdown("""
<p style="font-size:13px;color:var(--muted);margin-bottom:2px;">How it matches songs</p>
<div class="chip-row">
  <span class="chip">5 retrieval strategies</span>
  <span class="chip">Cosine similarity</span>
  <span class="chip">Popularity re-ranking</span>
  <span class="chip">Feedback re-ranking</span>
  <span class="chip">Artist-diversity cap</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
evaluator_id = st.session_state.evaluator_id
st.sidebar.caption(f"Evaluator ID: `{evaluator_id}`")

st.sidebar.divider()
strategy_key = st.sidebar.selectbox(
    "Retrieval strategy",
    list(STRATEGIES.keys()),
    format_func=lambda k: STRATEGIES[k][0],
    help="Which candidate pool + ranking logic to use. Every vote you give "
         "is tagged with this strategy so results are comparable per-strategy "
         "in the Aggregate relevance table below.",
)
st.sidebar.caption(STRATEGIES[strategy_key][1])

# ---------- Search filters ----------
st.markdown("### 🔎 Find a song")
left,right=st.columns(2)

with left:

    genre=st.selectbox(

        "Genre",

        ["All"]+sorted(df.track_genre.unique())

    )

filtered=df.copy()

if genre!="All":

    filtered=filtered[
        filtered.track_genre==genre
    ]

filtered = filtered.copy()

filtered["display"] = (
    filtered["track_name"]
    + " — "
    + filtered["artists"]
)

with right:

    search_term = st.text_input(
        "Search song",
        placeholder="Start typing a song or artist name..."
    )

# Rendering every song in one dropdown freezes the browser tab — search first,
# then only ever show a short matching list.
MAX_OPTIONS = 200

if not search_term:
    st.info("👆 Start typing above to search the song library.")
    st.stop()

matches = filtered[
    filtered["display"].str.contains(search_term, case=False, na=False)
]

if matches.empty:
    st.warning("No songs match that search — try a different spelling.")
    st.stop()

if len(matches) > MAX_OPTIONS:
    st.caption(
        f"Showing {MAX_OPTIONS} of {len(matches):,} matches — narrow your search for more precise results."
    )
    matches = matches.iloc[:MAX_OPTIONS]

selected = st.selectbox(
    "Choose a song",
    sorted(matches["display"])
)

selected_row = filtered[
    filtered["display"] == selected
].iloc[0]

selected_song = selected_row["track_name"]
selected_artist = selected_row["artists"]

top_n = st.slider(

"Number of recommendations",

5,

20,

10
)

recommend_clicked = st.button(
    "🎧 Generate Recommendations",
    use_container_width=True
)

@st.cache_resource
def get_scaled_features():
    # Scale the whole dataset once (O(n) memory) instead of per-cluster.
    # Similarity for a query song is computed on demand (1 x N), never a
    # precomputed N x N matrix — that's what made the old approach need a
    # KMeans pre-filter in the first place.
    return scaler.transform(df[feature_columns])

X_scaled = get_scaled_features()

@st.cache_data(ttl=60)
def get_feedback_df():
    # Cached for 60s: reused by the learned re-ranker, the heuristic
    # fallback, and the aggregate relevance table below — one Supabase
    # query serves all three instead of one each.
    return load_feedback()

def apply_feedback_boost(pool_df, pool_scaled, similarity):
    """
    Boost the pool's ranking using real evaluator feedback.

    Once there is enough labeled feedback (utils.reranker.MIN_FEEDBACK_FOR_MODEL
    rows, with both relevant and not_relevant votes present), a logistic
    regression trained on that feedback (audio features -> relevant/not)
    supplies the boost — it learns which audio traits evaluators actually
    respond to, instead of us guessing a fixed weight.

    Below that threshold, falls back to the original heuristic: a song's
    own historical relevance rate across past votes, centered at 0 so "no
    feedback yet" truly means no nudge either way.

    Returns (boost_array, used_learned_model: bool) — the bool is only
    used to show an honest status caption in the UI, not for scoring.
    """
    feedback_df = get_feedback_df()

    boost, used_model = get_learned_boost(feedback_df, pool_scaled, df, X_scaled)
    if used_model:
        return boost - 0.5, True

    if feedback_df.empty:
        return np.zeros(len(pool_df)), False

    labels = pool_df["track_name"] + " — " + pool_df["artists"]
    rate_by_song = feedback_df.groupby("recommended_song")["vote"].apply(
        lambda votes: (votes == "relevant").mean()
    )
    boost = labels.map(rate_by_song) - 0.5
    return boost.fillna(0.0).to_numpy(), False

def build_pool(selected_row, strategy):
    """
    Select the candidate pool for a given strategy. This is the only thing
    that differs strategy-to-strategy — ranking (similarity + popularity +
    feedback) is identical across all five so the comparison is fair (same
    scoring, different candidate sets is what's actually being evaluated).
    """
    song_genre = selected_row["track_genre"]
    song_cluster = selected_row["cluster"]

    if strategy == "genre_filtered":
        pool_df = df[df["track_genre"] == song_genre]
    elif strategy == "kmeans_restricted":
        pool_df = df[df["cluster"] == song_cluster]
    elif strategy == "hybrid":
        pool_df = df[(df["track_genre"] == song_genre) & (df["cluster"] == song_cluster)]
    else:
        # "global_cosine" and "popularity_weighted" both search the full
        # catalogue — popularity_weighted differs only in its scoring weight,
        # applied by the caller.
        pool_df = df

    # A tight filter (kmeans_restricted / hybrid) can occasionally leave too
    # few candidates to fill n results after de-duping/artist-capping — fall
    # back to the full catalogue rather than returning a near-empty list.
    if len(pool_df) < 5:
        pool_df = df

    return pool_df


def recommend(song_name, n=10, strategy="global_cosine", popularity_weight=0.10, feedback_weight=0.05, max_per_artist=2):
    """
    Retrieval-strategy-aware recommender. strategy selects the candidate
    pool (see build_pool); ranking logic is shared across strategies so the
    per-strategy relevance-rate comparison (utils/feedback.relevance_rate)
    reflects pool selection, not a different scoring method.

    strategy            : one of STRATEGIES' keys.
    popularity_weight   : small re-rank nudge on top of audio similarity,
                          overridden higher for the "popularity_weighted"
                          strategy specifically (see below).
    feedback_weight      : small re-rank nudge from historical evaluator
                          feedback (see apply_feedback_boost). Set to 0 to
                          fall back to pure similarity + popularity ranking.
    max_per_artist      : caps how many songs from one artist can appear in
                          the results (artist-diversity constraint).
    """

    try:
        selected_row = df[
            (df["track_name"] == song_name) &
            (df["artists"] == selected_artist)
        ].iloc[0]
        idx = selected_row.name
    except IndexError:
        return []

    query_pos = df.index.get_loc(idx)
    query_vec = X_scaled[query_pos].reshape(1, -1)

    pool_df = build_pool(selected_row, strategy)

    if strategy == "popularity_weighted":
        # A genuinely distinct strategy, not a minor variant of
        # global_cosine: popularity dominates the final ranking instead of
        # being a small nudge.
        popularity_weight = 0.45

    pool_positions = df.index.get_indexer(pool_df.index)
    pool_scaled = X_scaled[pool_positions]

    similarity = cosine_similarity(query_vec, pool_scaled).flatten()

    pop = pool_df["popularity"].to_numpy(dtype=float)
    pop_range = pop.max() - pop.min()
    pop_norm = (pop - pop.min()) / pop_range if pop_range > 0 else np.zeros_like(pop)

    feedback_boost, reranker_active = apply_feedback_boost(pool_df, pool_scaled, similarity)
    st.session_state["_reranker_active"] = reranker_active

    base_weight = 1 - popularity_weight - feedback_weight
    final_score = (
        base_weight * similarity
        + popularity_weight * pop_norm
        + feedback_weight * feedback_boost
    )

    order = np.argsort(-final_score)

    recommendations = []
    seen = set()
    artist_count = {}

    for pos in order:

        song = pool_df.iloc[pos]

        if song.name == idx:
            continue  # skip the query song itself (matched by index, not just name)

        key = (song.track_name, song.artists)

        if key in seen:
            continue

        primary_artist = song.artists.split(";")[0]

        if artist_count.get(primary_artist, 0) >= max_per_artist:
            continue

        seen.add(key)
        artist_count[primary_artist] = artist_count.get(primary_artist, 0) + 1

        recommendations.append((song, final_score[pos]))

        if len(recommendations) == n:
            break

    return recommendations

if recommend_clicked:

    with st.spinner("Finding similar songs... 🎵"):

        songs = recommend(
            selected_song,
            top_n,
            strategy=strategy_key,
        )

    # Stored in session_state rather than used directly: clicking a 👍/👎
    # button below triggers a Streamlit rerun, and recommend_clicked (a
    # plain st.button) would go back to False on that rerun, wiping the
    # results out from under the person mid-vote if we didn't persist them.
    # strategy_used is captured here too so the label + logged feedback stay
    # tied to whatever strategy was picked at the moment of search, even if
    # the sidebar selection changes before voting.
    st.session_state["current_songs"] = songs
    st.session_state["current_query_display"] = selected
    st.session_state["current_selected_song"] = selected_song
    st.session_state["current_strategy"] = strategy_key

if "current_songs" in st.session_state:

    songs = st.session_state["current_songs"]
    strategy_used = st.session_state["current_strategy"]

    if not songs:
        st.warning("Couldn't find that song in the dataset.")
    else:
        st.markdown(f"### ✨ Because you liked *{st.session_state['current_selected_song']}*")
        st.caption(f"Strategy: **{STRATEGIES[strategy_used][0]}**")

        fb_count = len(get_feedback_df())
        if st.session_state.get("_reranker_active"):
            st.caption(f"🧠 Learned re-ranker active — trained on {fb_count} votes")
        else:
            st.caption(
                f"📊 Using heuristic feedback boost — {fb_count}/{MIN_FEEDBACK_FOR_MODEL} "
                "votes needed (with both 👍 and 👎 present) before the learned re-ranker activates"
            )

        # Cards render through st.columns (not one big HTML grid) so the
        # 👍/👎 buttons underneath are real Streamlit widgets — raw HTML
        # <button> tags inside an st.markdown block can't trigger a Python
        # callback, so a single injected grid can't carry working feedback.
        N_COLS = 4
        song_rows = [songs[i:i + N_COLS] for i in range(0, len(songs), N_COLS)]

        for song_row in song_rows:
            cols = st.columns(N_COLS)
            for col, (row, score) in zip(cols, song_row):
                with col:
                    image = get_album_cover(row.track_name, row.artists)
                    if not image:
                        image = DEFAULT_IMAGE

                    match_pct = min(int(round(score * 100)), 99)

                    st.markdown(f"""
<div class="poster-card">
  <div class="poster-image" style="background-image:url('{image}')">
    <div class="poster-badge">{match_pct} match</div>
    <div class="poster-scrim">
      <h4>{row.track_name}</h4>
      <p>{row.artists}</p>
    </div>
  </div>
  <div class="poster-meta">
    <span class="genre-chip">{row.track_genre}</span>
    <span class="pop-meta">⭐ {row.popularity} popularity</span>
  </div>
</div>
""", unsafe_allow_html=True)

                    song_key = f"{row.track_name}_{row.artists}".replace(" ", "_")
                    recommended_song_label = f"{row.track_name} — {row.artists}"

                    fb_up, fb_down = st.columns(2)
                    if fb_up.button("👍", key=f"up_{song_key}", use_container_width=True):
                        log_feedback(
                            query_song=st.session_state["current_query_display"],
                            strategy=strategy_used,
                            recommended_song=recommended_song_label,
                            vote="relevant",
                            evaluator=evaluator_id,
                        )
                        st.toast("Feedback recorded ✅")
                    if fb_down.button("👎", key=f"down_{song_key}", use_container_width=True):
                        log_feedback(
                            query_song=st.session_state["current_query_display"],
                            strategy=strategy_used,
                            recommended_song=recommended_song_label,
                            vote="not_relevant",
                            evaluator=evaluator_id,
                        )
                        st.toast("Feedback recorded ✅")

        if st.session_state.get("_cover_error"):
            with st.expander("⚠️ Album art isn't loading — why?"):
                st.code(st.session_state["_cover_error"])

        with st.expander("📊 Aggregate relevance so far (all evaluators)"):
            agg = relevance_rate(get_feedback_df())
            if agg.empty:
                st.caption("No feedback logged yet — vote 👍/👎 above to populate this.")
            else:
                st.dataframe(agg, use_container_width=True, hide_index=True)

st.divider()

st.markdown("""
<div style="text-align:center;color:var(--muted);font-size:13px;">

Built using Streamlit • Global nearest-neighbour matching • Spotify API

<br><br>

Developed by <b style="color:var(--text);">Anshika Jain</b>

</div>
""", unsafe_allow_html=True)