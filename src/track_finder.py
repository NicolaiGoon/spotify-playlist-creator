import time
import difflib
from .text_utils import clean_title, greek_to_greeklish

class TrackFinder:
    def __init__(self, sp_client):
        """
        Initializes the TrackFinder with a Spotipy client.
        
        :param sp_client: An authenticated Spotipy client instance.
        """
        self.sp = sp_client

    def _build_search_query(self, title_to_search, artist_to_search):
        """Build a search query for Spotify."""
        query_parts = []
        if title_to_search:
            query_parts.append(f'track:"{title_to_search}"')
        if artist_to_search:
            query_parts.append(f'artist:"{artist_to_search}"')
        
        if not query_parts:
            return None

        if len(query_parts) == 1:
            if title_to_search:
                return f'"{title_to_search}"'
            if artist_to_search:
                return f'"{artist_to_search}"'
                
        return ' '.join(query_parts)

    def _calculate_match_score(self, local_song_info, spotify_track_info):
        """Calculate a match score between local song info and a Spotify track."""
        score = 0.0
        cleaned_local_title = clean_title(local_song_info.get('title', '')).lower()
        spotify_title = spotify_track_info.get('name', '').lower()
        
        title_similarity = difflib.SequenceMatcher(None, cleaned_local_title, spotify_title).ratio()
        score += title_similarity * 0.6

        local_artist = local_song_info.get('artist', '').lower()
        spotify_artists = [artist['name'].lower() for artist in spotify_track_info.get('artists', [])]
        
        if local_artist and spotify_artists:
            artist_similarity = max([difflib.SequenceMatcher(None, local_artist, sp_artist).ratio() for sp_artist in spotify_artists])
            score += artist_similarity * 0.4
        
        local_duration_ms = local_song_info.get('duration_ms', 0)
        spotify_duration_ms = spotify_track_info.get('duration_ms', 0)
        if local_duration_ms and spotify_duration_ms:
            duration_diff = abs(local_duration_ms - spotify_duration_ms)
            if duration_diff < 5000: # 5 seconds tolerance
                score += 0.1 # Bonus for close duration
        
        return score

    def _process_search_queries_for_stage(self, song_info, queries_to_try, best_match_candidate, highest_score_achieved, api_requests_count):
        """Helper function to process a list of search queries for a given stage."""
        for query in queries_to_try:
            if not query: continue
            
            api_requests_count += 1
            results = self.sp.search(q=query, type='track', limit=5)
            
            for item in results['tracks']['items']:
                spotify_track_info = {
                    'name': item['name'],
                    'artists': item['artists'],
                    'duration_ms': item['duration_ms'],
                    'uri': item['uri']
                }
                score = self._calculate_match_score(song_info, spotify_track_info)
                if score > highest_score_achieved:
                    highest_score_achieved = score
                    best_match_candidate = item
                    best_match_candidate['artist'] = ', '.join([a['name'] for a in item['artists']])

            time.sleep(0.1)
        return best_match_candidate, highest_score_achieved, api_requests_count

    def _get_stage1_queries(self, original_cleaned_title, artist):
        """Generate search queries for Stage 1 (High-Precision)."""
        return [self._build_search_query(original_cleaned_title, artist)]

    def _get_stage2_queries(self, original_cleaned_title, artist):
        """Generate search queries for Stage 2 (Primary Alternatives)."""
        queries = [
            self._build_search_query(original_cleaned_title, None),
            self._build_search_query(None, artist)
        ]
        return list(filter(None, queries))

    def _get_stage3_queries(self, original_cleaned_title, artist, greeklish_cleaned_title, greeklish_artist, stage1_queries, stage2_queries):
        """Generate unique search queries for Stage 3 (Fallback Searches)."""
        stage3_queries = []
        
        # Greeklish variations
        if greeklish_cleaned_title != original_cleaned_title or greeklish_artist != artist:
            stage3_queries.append(self._build_search_query(greeklish_cleaned_title, greeklish_artist))
            stage3_queries.append(self._build_search_query(greeklish_cleaned_title, None))
        
        # Title only (if not already in stage 2)
        title_only_query = self._build_search_query(original_cleaned_title, None)
        if title_only_query not in stage2_queries:
            stage3_queries.append(title_only_query)
            
        # Artist only (if not already in stage 2)
        artist_only_query = self._build_search_query(None, artist)
        if artist_only_query not in stage2_queries:
            stage3_queries.append(artist_only_query)

        # Remove duplicates and queries already tried
        all_tried_queries = set(stage1_queries + stage2_queries)
        unique_stage3_queries = [q for q in stage3_queries if q and q not in all_tried_queries]
        
        return unique_stage3_queries

    def search_spotify_track(self, song_info):
        """Search for a track on Spotify with improved matching, scoring, and staged early exit."""
        original_title = song_info.get('title', '')
        artist = song_info.get('artist', '')
        
        original_cleaned_title = clean_title(original_title)
        greeklish_cleaned_title = greek_to_greeklish(original_cleaned_title)
        greeklish_artist = greek_to_greeklish(artist)

        best_match_candidate = None
        highest_score_achieved = 0.0
        api_requests_count = 0

        # Stage 1: High-Precision Search
        stage1_queries = self._get_stage1_queries(original_cleaned_title, artist)
        best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
            song_info, stage1_queries, best_match_candidate, highest_score_achieved, api_requests_count
        )
        if highest_score_achieved > 0.95:
            return best_match_candidate

        # Stage 2: Primary Alternatives
        stage2_queries = self._get_stage2_queries(original_cleaned_title, artist)
        best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
            song_info, stage2_queries, best_match_candidate, highest_score_achieved, api_requests_count
        )
        if highest_score_achieved > 0.90:
            return best_match_candidate

        # Stage 3: Fallback Searches
        stage3_queries = self._get_stage3_queries(original_cleaned_title, artist, greeklish_cleaned_title, greeklish_artist, stage1_queries, stage2_queries)
        best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
            song_info, stage3_queries, best_match_candidate, highest_score_achieved, api_requests_count
        )

        # Final decision based on the best score found
        if highest_score_achieved > 0.7: # Confidence threshold
            return best_match_candidate
        
        return None
