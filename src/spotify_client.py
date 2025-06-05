import os
import re
import difflib
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .metadata_utils import get_audio_files, get_song_info # Relative import

class SpotifyPlaylistCreator:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        self.scope = 'playlist-modify-public playlist-modify-private'
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        ))

    # Note: get_audio_files and get_song_info are now imported from metadata_utils
    # and will be called as functions, not methods of this class, where needed.

    def _clean_title(self, title):
        """Clean and normalize the track title for better search results."""
        if not title:
            return ""
            
        patterns_to_remove = [
            r'\s*\(.*lyric.*\)',
            r'\s*\[.*\]',
            r'\s*\(.*official.*\)',
            r'\s*\(?official.*video\)?',
            r'\s*\(?official.*audio\)?',
            r'\b(HD|HQ|4K|1080p|720p)\b',
            r'\s*[-–]\s*(lyrics?|official|video|audio|HD|HQ|4K|1080p|720p).*$',
            r'\s*\([^)]*[α-ωΑ-Ω][^)]*\)',
            r'\[.*[α-ωΑ-Ω].*\]',
        ]
        
        cleaned = title.strip()
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _greek_to_greeklish(self, text):
        """Convert Greek characters to Greeklish."""
        if not text:
            return ""
            
        greek_to_greeklish = {
            'α': 'a', 'ά': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'έ': 'e',
            'ζ': 'z', 'η': 'i', 'ή': 'i', 'θ': 'th', 'ι': 'i', 'ί': 'i', 'ϊ': 'i',
            'ΐ': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
            'ό': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y',
            'ύ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o', 'ώ': 'o',
            'Α': 'A', 'Ά': 'A', 'Β': 'V', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Έ': 'E',
            'Ζ': 'Z', 'Η': 'I', 'Ή': 'I', 'Θ': 'Th', 'Ι': 'I', 'Ί': 'I', 'Ϊ': 'I',
            'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Ό': 'O',
            'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Ύ': 'Y', 'Φ': 'F',
            'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O', 'Ώ': 'O'
        }
        
        return ''.join(greek_to_greeklish.get(c, c) for c in text)
    
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
        cleaned_local_title = self._clean_title(local_song_info.get('title', '')).lower()
        spotify_title = spotify_track_info.get('name', '').lower()
        title_similarity = difflib.SequenceMatcher(None, cleaned_local_title, spotify_title).ratio()
        score += title_similarity * 0.6

        local_artist_str = local_song_info.get('artist', '').lower()
        spotify_artist_names = [a['name'].lower() for a in spotify_track_info.get('artists', [])]

        if local_artist_str and spotify_artist_names:
            local_artist_parts = [part.strip() for part in re.split(r',|ft\.|feat\.|&|και|με', local_artist_str)]
            local_artist_parts = [p for p in local_artist_parts if p]
            
            if local_artist_parts: # Simplified: removed the 'if not local_artist_parts: pass' block
                matched_local_parts = 0
                # Combine all spotify artist names into a single string for easier checking
                # This is a simplification; more advanced matching might be needed for edge cases
                combined_spotify_artists = " ".join(spotify_artist_names)
                for local_part in local_artist_parts:
                    if local_part in combined_spotify_artists:
                        matched_local_parts += 1
                
                artist_match_ratio = matched_local_parts / len(local_artist_parts)
                score += artist_match_ratio * 0.4
        elif not local_artist_str and not spotify_artist_names:
            score += 0.4
        return score

    def _process_search_queries_for_stage(self, song_info, queries_to_try, best_match_candidate, highest_score_achieved, api_requests_count):
        """Helper function to process a list of search queries for a given stage."""
        for query in filter(None, queries_to_try):
            try:
                results = self.sp.search(q=query, type='track', limit=5)
                api_requests_count += 1
                if results and results['tracks']['items']:
                    for spotify_track_candidate in results['tracks']['items']:
                        current_score = self._calculate_match_score(song_info, spotify_track_candidate)
                        if current_score > highest_score_achieved:
                            highest_score_achieved = current_score
                            best_match_candidate = {
                                'id': spotify_track_candidate['id'],
                                'name': spotify_track_candidate['name'],
                                'artist': spotify_track_candidate['artists'][0]['name'],
                                'uri': spotify_track_candidate['uri']
                            }
            except Exception as e:
                print(f"Spotify API search error for query '{query}': {e}")
        return best_match_candidate, highest_score_achieved, api_requests_count

    def _get_stage1_queries(self, original_cleaned_title, artist):
        """Generate search queries for Stage 1 (High-Precision)."""
        return [self._build_search_query(original_cleaned_title, artist)]

    def _get_stage2_queries(self, original_cleaned_title, artist):
        """Generate search queries for Stage 2 (Primary Alternatives)."""
        queries = [self._build_search_query(original_cleaned_title, '')]
        if artist:
            queries.append(self._build_search_query('', artist))
        return queries

    def _get_stage3_queries(self, original_cleaned_title, artist, greeklish_cleaned_title, greeklish_artist, stage1_queries, stage2_queries):
        """Generate unique search queries for Stage 3 (Fallback Searches)."""
        queries = []
        if greeklish_cleaned_title != original_cleaned_title:
            queries.append(self._build_search_query(greeklish_cleaned_title, artist))
            queries.append(self._build_search_query(greeklish_cleaned_title, ''))
            if artist and greeklish_artist != artist:
                queries.append(self._build_search_query(greeklish_cleaned_title, greeklish_artist))
        
        if artist and greeklish_artist != artist:
            queries.append(self._build_search_query(original_cleaned_title, greeklish_artist))

        # Raw string queries for broader matching
        if artist:
            queries.append(f'\"{original_cleaned_title}\" \"{artist}\"')
        queries.append(f'\"{original_cleaned_title}\"')
        if artist:
            queries.append(f'\"{artist}\"')
        if greeklish_cleaned_title != original_cleaned_title:
            if artist and greeklish_artist != artist:
                queries.append(f'\"{greeklish_cleaned_title}\" \"{greeklish_artist}\"')
            elif artist:
                queries.append(f'\"{greeklish_cleaned_title}\" \"{artist}\"')
            queries.append(f'\"{greeklish_cleaned_title}\"')
        
        # Remove duplicate queries that might have been covered by earlier stages or builder
        processed_queries = set(filter(None, stage1_queries + stage2_queries))
        unique_queries = [q for q in filter(None, queries) if q not in processed_queries]
        return unique_queries

    def search_spotify_track(self, song_info):
        """Search for a track on Spotify with improved matching, scoring, and staged early exit."""
        start_time = time.time()
        api_requests_count = 0

        title = song_info.get('title', '').strip()
        artist = song_info.get('artist', '').strip()

        if not title:
            end_time = time.time()
            time_taken = end_time - start_time
            log_title = title if title else song_info.get('file_path', 'Unknown Title') 
            log_artist = artist if artist else 'Unknown Artist'
            print(f"INFO: Search for '{log_title} - {log_artist}' took {time_taken:.2f}s, {api_requests_count} API_req(s). Result: Not Found (No title)")
            return None

        original_cleaned_title = self._clean_title(title)
        greeklish_cleaned_title = self._greek_to_greeklish(original_cleaned_title)
        greeklish_artist = self._greek_to_greeklish(artist)

        best_match_candidate = None
        highest_score_achieved = 0.0

        STAGE1_MIN_SCORE = 0.85
        STAGE2_MIN_SCORE = 0.75
        MIN_ACCEPTABLE_SCORE = 0.65

        # Stage 1
        stage1_queries = self._get_stage1_queries(original_cleaned_title, artist)
        best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
            song_info, stage1_queries, best_match_candidate, highest_score_achieved, api_requests_count
        )
        if best_match_candidate and highest_score_achieved >= STAGE1_MIN_SCORE:
            end_time = time.time()
            print(f"INFO: Search for '{title} - {artist}' took {end_time - start_time:.2f}s, {api_requests_count} API_req(s). Result: Found (Stage 1)")
            return best_match_candidate

        # Stage 2
        stage2_queries = self._get_stage2_queries(original_cleaned_title, artist)
        best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
            song_info, stage2_queries, best_match_candidate, highest_score_achieved, api_requests_count
        )
        if best_match_candidate and highest_score_achieved >= STAGE2_MIN_SCORE:
            end_time = time.time()
            print(f"INFO: Search for '{title} - {artist}' took {end_time - start_time:.2f}s, {api_requests_count} API_req(s). Result: Found (Stage 2)")
            return best_match_candidate

        # Stage 3
        stage3_queries = self._get_stage3_queries(original_cleaned_title, artist, greeklish_cleaned_title, greeklish_artist, stage1_queries, stage2_queries)
        if stage3_queries:
            best_match_candidate, highest_score_achieved, api_requests_count = self._process_search_queries_for_stage(
                song_info, stage3_queries, best_match_candidate, highest_score_achieved, api_requests_count
            )

        end_time = time.time()
        time_taken = end_time - start_time
        if best_match_candidate and highest_score_achieved >= MIN_ACCEPTABLE_SCORE:
            print(f"INFO: Search for '{title} - {artist}' took {time_taken:.2f}s, {api_requests_count} API_req(s). Result: Found (Stage 3)")
            return best_match_candidate
        else:
            print(f"INFO: Search for '{title} - {artist}' took {time_taken:.2f}s, {api_requests_count} API_req(s). Result: Not Found")
            return None
    
    def create_playlist(self, name, public=True, description=None):
        """Create a new playlist."""
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
        """Add tracks to a playlist."""
        if not track_uris:
            print("No tracks to add.")
            return

        # Spotify API allows adding 100 tracks at a time
        for i in range(0, len(track_uris), 100):
            self.sp.playlist_add_items(playlist_id, track_uris[i:i+100])
        print(f"Added {len(track_uris)} tracks to the playlist.")

    def _process_audio_files(self, audio_files):
        """Process audio files to find them on Spotify."""
        found_tracks_uris = []
        not_found_tracks_info = []
        for audio_file in audio_files:
            song_info = get_song_info(audio_file) # Assumes get_song_info is imported from metadata_utils
            track = self.search_spotify_track(song_info)
            if track:
                found_tracks_uris.append(track['uri'])
                print(f"✓ Found: {track['name']} - {track['artist']}")
            else:
                not_found_tracks_info.append(song_info)
                display_title = song_info.get('title') or os.path.basename(audio_file)
                display_artist = song_info.get('artist') or "Unknown Artist"
                print(f"✗ Not found: {display_title} - {display_artist}")
        return found_tracks_uris, not_found_tracks_info

    def _print_summary(self, found_tracks_count, not_found_tracks_info):
        """Print a summary of tracks found and not found."""
        print("\n--- Summary ---")
        print(f"Found {found_tracks_count} tracks on Spotify.")
        print(f"{len(not_found_tracks_info)} tracks not found or below confidence threshold.")
        if not_found_tracks_info:
            print("\nTracks not found:")
            for item in not_found_tracks_info:
                display_title = item.get('title') or os.path.basename(item.get('file_path', ''))
                display_artist = item.get('artist') or "Unknown Artist"
                print(f"  - {display_title} - {display_artist}")

    def _handle_playlist_creation(self, playlist_name, public, found_tracks_uris, dry_run):
        """Handle the actual playlist creation or dry run output."""
        if not dry_run and found_tracks_uris:
            playlist = self.create_playlist(playlist_name, public=public)
            self.add_tracks_to_playlist(playlist['id'], found_tracks_uris)
            print(f"\nPlaylist '{playlist_name}' created/updated on Spotify with {len(found_tracks_uris)} tracks.")
        elif dry_run:
            print("\nDry run complete. No playlist created on Spotify.")
        elif not found_tracks_uris:
            print("\nNo tracks found on Spotify to create a playlist.")

    def create_playlist_from_folder(self, folder_path, playlist_name=None, public=True, dry_run=False):
        if not os.path.isdir(folder_path):
            raise ValueError(f"Directory not found: {folder_path}")
        
        if not playlist_name:
            playlist_name = os.path.basename(os.path.normpath(folder_path))
        
        if dry_run:
            print("\n=== DRY RUN MODE ===")
            print("No changes will be made to your Spotify account.\n")
        
        print(f"Scanning folder: {folder_path}")
        audio_files = get_audio_files(folder_path) # Assumes get_audio_files is imported
        
        if not audio_files:
            print("No audio files found in the folder.")
            return

        print(f"Found {len(audio_files)} audio files. Processing...")
        
        found_tracks_uris, not_found_tracks_info = self._process_audio_files(audio_files)
        
        self._print_summary(len(found_tracks_uris), not_found_tracks_info)
        
        self._handle_playlist_creation(playlist_name, public, found_tracks_uris, dry_run)
