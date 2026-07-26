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
#update it 
df = pd.read_csv("data/spotify_clustered_dataset.csv")
scaler = joblib.load("models/scaler.joblib")
kmeans = joblib.load("models/kmeans.joblib")

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

- KMeans Clustering
- Cosine Similarity
- StandardScaler
- 13 Audio Features
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
def build_scaled_clusters():
    # Store only each cluster's scaled feature matrix (O(n) memory),
    # not the full NxN similarity matrix (O(n^2) — blows up on large clusters).
    # Similarity is computed on-demand per query in recommend().
    scaled_dict = {}

    for cluster in sorted(df["cluster"].unique()):

        cluster_df = df[df["cluster"] == cluster]

        scaled_dict[cluster] = scaler.transform(
            cluster_df[feature_columns]
        )

    return scaled_dict

scaled_clusters = build_scaled_clusters()
    
def recommend(song_name, n=10, restrict_genre=None):

    try:
        selected_row = df[
        (df["track_name"] == song_name) &
        (df["artists"] == selected_artist)
    ].iloc[0]
        idx = selected_row.name
    except IndexError:
        return []

    cluster = df.loc[idx, "cluster"]

    cluster_df = df[df["cluster"] == cluster].copy()

    cluster_scaled = scaled_clusters[cluster]

    local_idx = cluster_df.index.get_loc(idx)

    similarity = cosine_similarity(
        cluster_scaled[local_idx].reshape(1, -1),
        cluster_scaled
    ).flatten()

    scores = list(enumerate(similarity))

    if restrict_genre and restrict_genre != "All":
        allowed_positions = set(
            cluster_df.index.get_loc(i)
            for i in cluster_df[cluster_df.track_genre == restrict_genre].index
        )
        scores = [(i, s) for i, s in scores if i in allowed_positions]

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    recommendations = []

    seen = set()

    for i, score in scores:

        song = cluster_df.iloc[i]

        key = (song.track_name, song.artists)

        if key in seen:
            continue

        seen.add(key)

        if song.track_name == song_name:
            continue

        recommendations.append((song, score))

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
    f"Similarity Score : {score*100:.1f}%"
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