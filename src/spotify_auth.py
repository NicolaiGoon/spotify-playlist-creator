import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_spotify_client():
    """Initializes and returns a Spotipy client."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
    scope = 'playlist-modify-public playlist-modify-private'
    
    if not client_id or not client_secret:
        raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
    
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=False
    )
    
    return spotipy.Spotify(auth_manager=auth_manager)
