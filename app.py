import streamlit as st
import pandas as pd
import numpy as np
import joblib
from spotify_api import get_album_cover
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(
    page_title="Music recommender: MUSICALLY",
    page_icon="🎵",
    layout="wide"
)

df = pd.read_csv("data/spotify_clustered_dataset.csv")
scaler = joblib.load("models/scaler.joblib")
kmeans = joblib.load("models/kmeans.joblib")  # kept for EDA/cluster count metric only

DEFAULT_IMAGE = "https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_CMYK_Green.png"

st.markdown("""
<style>

.stApp{
    background:#121212;
    color:white;
}

section[data-testid="stSidebar"]{
    background:#181818;
}

.block-container{
    padding-top:1.5rem;
}

.hero{
    background:linear-gradient(135deg,#1DB954,#191414);
    padding:35px;
    border-radius:18px;
    margin-bottom:25px;
}

.hero h1{
    color:white;
    text-align:center;
    font-size:50px;
}

.hero p{
    text-align:center;
    color:white;
}

.card{

    height:180px;
    display:flex;
    flex-direction:column;
    justify-content:center; 
    background:#181818;
    border-radius:18px;
    padding:18px;
    border:1px solid #2a2a2a;
    box-shadow:0 10px 25px rgba(0,0,0,.4);
    margin-bottom:20px;

}

img{

    border-radius:15px;

}

</style>""",
unsafe_allow_html=True
)

st.markdown("""
<div class="hero">
<h1>🎵 MUSICALLY</h1>
<p>Discover songs with similar audio characteristics instantly.</p>
</div>
""", unsafe_allow_html=True)

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

col1,col2,col3,col4=st.columns(4)

col1.metric("🎵 Songs", f"{len(df):,}")
col2.metric("🎼 Genres", df.track_genre.nunique())
col3.metric("📂 Clusters", df.cluster.nunique())
col4.metric("🎧 Features", len(feature_columns))

st.sidebar.title("🎵 MUSICALLY")

st.sidebar.success("Content-Based Recommendation")

st.sidebar.divider()

st.sidebar.metric("Songs", len(df))
st.sidebar.metric("Genres", df.track_genre.nunique())
st.sidebar.metric("Clusters", df.cluster.nunique())

st.sidebar.divider()

st.sidebar.markdown("""
### ⚙️ Model

- Global Nearest-Neighbour Search
- Cosine Similarity
- Genre-aware filtering
- Popularity re-ranking
- Artist-diversity cap
- StandardScaler
- 10 Audio Features
""")


st.markdown("## 🔎 Search Filters")
left,right=st.columns(2)

with left:

    genre=st.selectbox(

        "🎼 Genre",

        ["All"]+sorted(df.track_genre.unique())

    )

filtered=df.copy()

if genre!="All":

    filtered=filtered[
        filtered.track_genre==genre
    ]

with right:

    filtered = filtered.copy()

filtered["display"] = (
    filtered["track_name"]
    + " — "
    + filtered["artists"]
)

selected = st.selectbox(

    "🎵 Search Song",

    sorted(filtered["display"])

)

selected_row = filtered[
    filtered["display"] == selected
].iloc[0]

selected_song = selected_row["track_name"]
selected_artist = selected_row["artists"]

top_n = st.slider(

"Number of Recommendations",

5,

20,

10
)

stay_in_genre = st.checkbox(
    "Stay within selected genre",
    value=(genre != "All"),
    help="If checked, recommendations are pulled only from the selected genre. "
         "If unchecked, songs are matched purely on audio characteristics, "
         "which can surface similar-sounding tracks from other genres/languages."
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

def recommend(song_name, n=10, restrict_genre=None, popularity_weight=0.10, max_per_artist=2):
    """
    Global nearest-neighbour recommender — no KMeans gate.

    restrict_genre     : a specific genre string to restrict candidates to, or
                          None/"All" for a full-dataset search.
    popularity_weight   : small re-rank nudge on top of audio similarity, not
                          a popularity recommender.
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

    if restrict_genre and restrict_genre != "All":
        pool_df = df[df["track_genre"] == restrict_genre]
    else:
        pool_df = df

    pool_positions = df.index.get_indexer(pool_df.index)
    pool_scaled = X_scaled[pool_positions]

    similarity = cosine_similarity(query_vec, pool_scaled).flatten()

    pop = pool_df["popularity"].to_numpy(dtype=float)
    pop_range = pop.max() - pop.min()
    pop_norm = (pop - pop.min()) / pop_range if pop_range > 0 else np.zeros_like(pop)

    final_score = (1 - popularity_weight) * similarity + popularity_weight * pop_norm

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
        songs=recommend(
        selected_song,
        top_n,
        restrict_genre=genre if stay_in_genre else None
    )

    cols=st.columns(3)

    for idx,(row,score) in enumerate(songs):

        image = get_album_cover(
    row.track_name,
    row.artists
)
        if not image:
            image = DEFAULT_IMAGE

        with cols[idx%3]:

            if image:

                st.image(
                    image,
                    use_container_width=True
                )

            else:

                st.image(
                    DEFAULT_IMAGE,
                    use_container_width=True
                )
            st.progress(min(float(score),1.0))
            st.caption(
    f"Match Score : {score*100:.0f}"
)
            st.markdown(f"""
<div class="card">

<h4>{row.track_name}</h4>

<p>👤 <b>{row.artists}</b></p>

<p>🎼 {row.track_genre}</p>

<p>⭐ Popularity : {row.popularity}</p>

</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("""
<div style="text-align:center;color:gray">

Built using Streamlit • KMeans • Spotify API

<br><br>

Developed by <b>Anshika Jain</b>

</div>
""", unsafe_allow_html=True)