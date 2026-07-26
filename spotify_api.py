import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = "b12f48a5d15040a1af5705665b587162"
CLIENT_SECRET = "a060a44d7683450cb7cfb8c04cf2f2c4"

client_credentials_manager = SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager
)


def get_album_cover(song, artist):

    try:

        result = sp.search(
            q=f"track:{song} artist:{artist}",
            type="track",
            limit=1
        )

        items = result["tracks"]["items"]

        if len(items) > 0:

            return items[0]["album"]["images"][0]["url"]

        return None

    except:
        return None