import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


@st.cache_resource
def _get_client():
    client_credentials_manager = SpotifyClientCredentials(
        client_id=st.secrets["SPOTIFY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def get_album_cover(song, artist):

    try:

        sp = _get_client()

        result = sp.search(
            q=f"track:{song} artist:{artist}",
            type="track",
            limit=1
        )

        items = result["tracks"]["items"]

        if len(items) > 0:

            return items[0]["album"]["images"][0]["url"]

        return None

    except Exception:
        return None