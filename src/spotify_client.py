from .spotify_auth import get_spotify_client

class SpotifyClient:
    """
    A wrapper for the Spotipy client to interact with the Spotify API.
    """
    def __init__(self):
        """
        Initializes the Spotify Client using credentials from spotify_auth.
        """
        self.sp = get_spotify_client()

    def create_playlist(self, name, public=True, description=''):
        """
        Creates a new playlist on Spotify.

        :param name: The name of the playlist.
        :param public: If True, the playlist will be public.
        :param description: The description for the playlist.
        :return: The created playlist object from Spotify.
        """
        user_id = self.sp.me()['id']
        playlist = self.sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description
        )
        print(f"Playlist '{playlist['name']}' created successfully.")
        return playlist

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """
        Adds tracks to a specified Spotify playlist.

        :param playlist_id: The ID of the playlist.
        :param track_uris: A list of track URIs to add.
        """
        if not track_uris:
            print("No tracks to add.")
            return

        # The Spotify API allows adding a maximum of 100 tracks per request.
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i+100]
            self.sp.playlist_add_items(playlist_id, chunk)
        
        print(f"Added {len(track_uris)} tracks to the playlist.")
