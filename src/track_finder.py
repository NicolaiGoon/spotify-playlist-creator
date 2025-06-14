from .text_utils import clean_title, greek_to_greeklish, is_greek, clean_artist

class TrackFinder:
    def __init__(self, sp_client):
        """
        Initializes the TrackFinder with a Spotipy client.
        
        :param sp_client: An authenticated Spotipy client instance.
        """
        self.sp = sp_client

    def _build_search_query(self, title, artist):
        """Build a search query for Spotify, including only non-null fields."""
        query_parts = []
        if title:
            query_parts.append(f'track:"{title}"')
        if artist:
            query_parts.append(f'artist:"{artist}"')
        
        return ' '.join(query_parts) if query_parts else None

    def _perform_search(self, query):
        """Performs a search on Spotify and returns the first track found."""
        if not query:
            return None
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if results and results['tracks']['items']:
                track = results['tracks']['items'][0]
                track['artist'] = ', '.join([a['name'] for a in track['artists']])
                return track
        except Exception as e:
            print(f"Spotify API search error for query '{query}': {e}")
        return None

    def search_spotify_track(self, song_info):
        """
        Search for a track on Spotify using a simplified, two-attempt strategy.
        1. Search with original metadata (title, artist).
        2. If it fails and the track is in Greek, retry with Greeklish versions.
        The first result from the API is considered the match.
        """
        title = song_info.get('title', '')
        artist = song_info.get('artist', '')
        
        cleaned_title = clean_title(title)
        cleaned_artist = clean_artist(artist)

        # Attempt 1: Search with original, cleaned metadata
        query = self._build_search_query(cleaned_title, cleaned_artist)
        track = self._perform_search(query)
        if track:
            return track

        # Attempt 2: If it's a Greek song, try with Greeklish
        if is_greek(cleaned_title) or is_greek(cleaned_artist):
            greeklish_title = greek_to_greeklish(cleaned_title)
            greeklish_artist = greek_to_greeklish(cleaned_artist)
            
            if greeklish_title != cleaned_title or greeklish_artist != cleaned_artist:
                greeklish_query = self._build_search_query(greeklish_title, greeklish_artist)
                track = self._perform_search(greeklish_query)
                if track:
                    return track

        return None

