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
        return _cached_album_cover(song, artist)

    except Exception as e:
        # Keep the first real error around so it can be surfaced in the app
        # instead of silently falling back to the logo every time.
        st.session_state.setdefault("_cover_error", str(e))
        return None


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _cached_album_cover(song, artist):
    # Note: this must raise (not catch-and-return-None) on failure. If it
    # returned None on auth/network errors, st.cache_data would cache that
    # None permanently — a genuine "no match" result and a temporary auth
    # failure need to be treated differently, so only real "no match" is
    # returned/cached here; everything else propagates up uncached.

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