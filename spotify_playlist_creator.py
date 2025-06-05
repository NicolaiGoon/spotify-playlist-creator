import os
import re
import difflib
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from pathlib import Path
from mutagen import File as MutagenFile
import time

# Common audio file extensions to look for
AUDIO_EXTENSIONS = {
    # Common formats
    '.mp3', '.m4a', '.m4b', '.m4p', '.mp4', '.flac', 
    # Less common but still widely used
    '.ogg', '.oga', '.opus', '.wav', '.wave', '.aif', 
    '.aiff', '.aifc', '.wma', '.asf', '.ape', '.mpc', 
    '.mp+', '.wv', '.tta'
}

# Load environment variables from .env file
load_dotenv()

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
    
    def get_audio_files(self, folder_path):
        """Get list of audio files from the specified folder."""
        return [f for f in Path(folder_path).rglob('*') if f.suffix.lower() in AUDIO_EXTENSIONS]
    
    def get_song_info(self, file_path):
        """Extract song information from audio file metadata."""
        file_path = Path(file_path)
        file_path_str = str(file_path)
        
        # Default values
        metadata = {
            'title': file_path.stem,
            'artist': '',
            'album': '',
            'file_path': file_path_str
        }
        
        try:
            # Try to load the file with Mutagen
            audio = MutagenFile(file_path_str, easy=True)
            
            if audio is not None and hasattr(audio, 'tags') and audio.tags is not None:
                # Common tag names across different formats
                tag_mapping = {
                    'title': ['title', 'TIT2', '\xa9nam'],
                    'artist': ['artist', 'TPE1', '\xa9ART'],
                    'album': ['album', 'TALB', '\xa9alb']
                }
                
                # Try different tag names for each field
                for field, tag_names in tag_mapping.items():
                    for tag in tag_names:
                        try:
                            if tag in audio.tags:
                                value = audio.tags[tag]
                                # Handle different tag value formats
                                if isinstance(value, list):
                                    if value:  # If list is not empty
                                        value = str(value[0])
                                    else:
                                        continue
                                else:
                                    value = str(value)
                                
                                if value.strip():
                                    metadata[field] = value.strip()
                                    break  # Found a valid value, move to next field
                        except (KeyError, IndexError, AttributeError):
                            continue
            
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")
        
        return metadata
    
    def _clean_title(self, title):
        """Clean and normalize the track title for better search results."""
        if not title:
            return ""
            
        # Common patterns to remove from titles
        patterns_to_remove = [
            r'\s*\(.*lyric.*\)',       # (lyrics), (lyric video), etc.
            r'\s*\[.*\]',               # [Official Video], [Audio], etc.
            r'\s*\(.*official.*\)',     # (Official Audio), etc.
            r'\s*\(?official.*video\)?',
            r'\s*\(?official.*audio\)?',
            r'\b(HD|HQ|4K|1080p|720p)\b',
            r'\s*[-–]\s*(lyrics?|official|video|audio|HD|HQ|4K|1080p|720p).*$',
            r'\s*\([^)]*[α-ωΑ-Ω][^)]*\)',  # Greek text in parentheses
            r'\[.*[α-ωΑ-Ω].*\]',            # Greek text in square brackets
        ]
        
        cleaned = title.strip()
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
        # Remove multiple spaces and trim
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
            'ύ': 'y', 'ϋ': 'y', 'ΰ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
            'ώ': 'o', 'Α': 'A', 'Ά': 'A', 'Β': 'V', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E',
            'Έ': 'E', 'Ζ': 'Z', 'Η': 'I', 'Ή': 'I', 'Θ': 'TH', 'Ι': 'I', 'Ί': 'I',
            'Ϊ': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O',
            'Ό': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Ύ': 'Y',
            'Ϋ': 'Y', 'Φ': 'F', 'Χ': 'CH', 'Ψ': 'PS', 'Ω': 'O', 'Ώ': 'O'
        }
        
        return ''.join(greek_to_greeklish.get(c, c) for c in text)
    
    def _build_search_query(self, title_to_search, artist_to_search):
        """Build a search query for Spotify."""
        query_parts = []
        # Use exact phrase matching for better precision
        if title_to_search:
            query_parts.append(f'track:"{title_to_search}"')
        if artist_to_search:
            query_parts.append(f'artist:"{artist_to_search}"')
        
        if not query_parts:
            return None

        # If only one part is available, a general search might be better
        # to catch cases where metadata might be in the wrong field or mixed.
        if len(query_parts) == 1:
            if title_to_search:
                return f'"{title_to_search}"'
            if artist_to_search:
                return f'"{artist_to_search}"'
                
        return ' '.join(query_parts)

    def _calculate_match_score(self, local_song_info, spotify_track_info):
        """Calculate a match score between local song info and a Spotify track."""
        score = 0.0
        
        # Title similarity (weighted 60%)
        cleaned_local_title = self._clean_title(local_song_info.get('title', '')).lower()
        spotify_title = spotify_track_info.get('name', '').lower()
        title_similarity = difflib.SequenceMatcher(None, cleaned_local_title, spotify_title).ratio()
        score += title_similarity * 0.6

        # Artist similarity (weighted 40%)
        local_artist_str = local_song_info.get('artist', '').lower()
        spotify_artist_names = [a['name'].lower() for a in spotify_track_info.get('artists', [])]

        if local_artist_str and spotify_artist_names:
            # Split local artist string by common separators like ',', 'ft.', 'feat.', '&', 'και', 'με'
            # and remove empty strings that might result from splitting.
            local_artist_parts = [part.strip() for part in re.split(r',|ft\.|feat\.|&|και|με', local_artist_str)]
            local_artist_parts = [p for p in local_artist_parts if p] # Ensure no empty parts

            if not local_artist_parts: # If after splitting, it's empty (e.g. artist was just ',')
                pass # No artist info to match, rely on title
            else:
                matched_local_parts = 0
                for local_part in local_artist_parts:
                    if any(local_part in sp_artist for sp_artist in spotify_artist_names):
                        matched_local_parts += 1
                
                # Score based on proportion of matched local artist parts
                if local_artist_parts: # Avoid division by zero
                    artist_match_ratio = matched_local_parts / len(local_artist_parts)
                    score += artist_match_ratio * 0.4
        elif not local_artist_str and not spotify_artist_names: # Both have no artist info
            score += 0.4 # Consider it a full artist match (or non-applicable penalty)
            
        return score

    def search_spotify_track(self, song_info):
        """Search for a track on Spotify with improved matching, scoring, and staged early exit."""
        start_time = time.time()
        api_requests_count = 0

        title = song_info.get('title', '').strip()
        artist = song_info.get('artist', '').strip()

        if not title:
            end_time = time.time()
            time_taken = end_time - start_time
            # Ensure title/artist are somewhat descriptive for the log, even if title is missing for search
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

        def _execute_queries(queries_to_try):
            nonlocal best_match_candidate, highest_score_achieved, api_requests_count
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
            return best_match_candidate, highest_score_achieved

        # Stage 1: High-Precision (Cleaned Title + Original Artist)
        stage1_queries = [self._build_search_query(original_cleaned_title, artist)]
        _execute_queries(stage1_queries)
        if best_match_candidate and highest_score_achieved >= STAGE1_MIN_SCORE:
            end_time = time.time()
            print(f"INFO: Search for '{title} - {artist}' took {end_time - start_time:.2f}s, {api_requests_count} API_req(s). Result: Found (Stage 1)")
            return best_match_candidate

        # Stage 2: Primary Alternatives (Cleaned Title only, Original Artist only)
        stage2_queries = [
            self._build_search_query(original_cleaned_title, ''),
        ]
        if artist:
            stage2_queries.append(self._build_search_query('', artist))
        _execute_queries(stage2_queries)
        if best_match_candidate and highest_score_achieved >= STAGE2_MIN_SCORE:
            end_time = time.time()
            print(f"INFO: Search for '{title} - {artist}' took {end_time - start_time:.2f}s, {api_requests_count} API_req(s). Result: Found (Stage 2)")
            return best_match_candidate

        # Stage 3: Fallback Searches (Greeklish, Broader Keywords)
        stage3_queries = []
        if greeklish_cleaned_title != original_cleaned_title:
            stage3_queries.append(self._build_search_query(greeklish_cleaned_title, artist))
            stage3_queries.append(self._build_search_query(greeklish_cleaned_title, ''))
            if artist and greeklish_artist != artist:
                stage3_queries.append(self._build_search_query(greeklish_cleaned_title, greeklish_artist))
        
        if artist and greeklish_artist != artist:
            stage3_queries.append(self._build_search_query(original_cleaned_title, greeklish_artist))

        if artist:
            stage3_queries.append(f'"{original_cleaned_title}" "{artist}"')
        stage3_queries.append(f'"{original_cleaned_title}"')
        if artist:
             stage3_queries.append(f'"{artist}"')
        if greeklish_cleaned_title != original_cleaned_title:
            if artist and greeklish_artist != artist:
                 stage3_queries.append(f'"{greeklish_cleaned_title}" "{greeklish_artist}"')
            elif artist:
                 stage3_queries.append(f'"{greeklish_cleaned_title}" "{artist}"')
            stage3_queries.append(f'"{greeklish_cleaned_title}"')
        
        # Remove duplicates that might have been covered in stage 1 or 2 implicitly by broader searches
        # This is a simple way; more robust would be to track exact queries already run.
        processed_queries = set(filter(None, stage1_queries + stage2_queries))
        unique_stage3_queries = [q for q in filter(None, stage3_queries) if q not in processed_queries]
        
        if unique_stage3_queries:
            _execute_queries(unique_stage3_queries)

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
            description=description or f"Playlist created from local music files on {os.path.basename(os.getcwd())}"
        )
        return playlist['id']
    
    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """Add tracks to a playlist."""
        # Spotify API allows adding up to 100 tracks per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            self.sp.playlist_add_items(playlist_id, batch)
    
    def create_playlist_from_folder(self, folder_path, playlist_name=None, public=True, dry_run=False):
        """
        Create a playlist from a folder of songs.
        
        Args:
            folder_path (str): Path to the folder containing audio files
            playlist_name (str, optional): Name for the playlist. Defaults to folder name.
            public (bool, optional): Whether the playlist should be public. Defaults to True.
            dry_run (bool, optional): If True, only shows what would be done without making changes. Defaults to False.
        """
        if not os.path.isdir(folder_path):
            raise ValueError(f"Directory not found: {folder_path}")
        
        if not playlist_name:
            playlist_name = os.path.basename(os.path.normpath(folder_path))
        
        if dry_run:
            print("\n=== DRY RUN MODE ===")
            print("No changes will be made to your Spotify account.\n")
        
        print(f"Scanning folder: {folder_path}")
        audio_files = self.get_audio_files(folder_path)
        
        if not audio_files:
            print("No audio files found in the specified folder.")
            return
            
        print(f"Found {len(audio_files)} audio files. Processing...")
        
        tracks = []
        found_tracks = []
        not_found = []
        
        for file_path in audio_files:
            song_info = self.get_song_info(file_path)
            track = self.search_spotify_track(song_info)
            
            if track:
                found_tracks.append(track)
                print(f"✓ Found: {track['name']} - {track['artist']}")
            else:
                not_found.append(song_info['title'])
                print(f"✗ Not found: {song_info['title']}")
        
        if not found_tracks:
            print("No tracks found on Spotify. Playlist not created.")
            return
        
        if dry_run:
            print("\n=== DRY RUN RESULTS ===")
            print(f"Would create playlist: '{playlist_name}'")
            print(f"Would add {len(found_tracks)} tracks to the playlist:")
            for i, track in enumerate(found_tracks, 1):
                print(f"  {i}. {track['name']} - {track['artist']}")
                
            if not_found:
                print(f"\nCould not find the following {len(not_found)} tracks on Spotify:")
                for title in not_found:
                    print(f"- {title}")
            
            print("\nDry run complete. No changes were made to your Spotify account.")
            return
            
        # If not in dry run mode, proceed with actual playlist creation
        print(f"\nCreating playlist with {len(found_tracks)} tracks...")
        playlist_id = self.create_playlist(
            name=playlist_name,
            public=public,
            description=f"Created from {len(found_tracks)} local music files"
        )
        
        track_uris = [track['uri'] for track in found_tracks]
        self.add_tracks_to_playlist(playlist_id, track_uris)
        
        print(f"\n✅ Playlist '{playlist_name}' created successfully!")
        print(f"Added {len(found_tracks)} tracks to the playlist.")
        
        if not_found:
            print(f"\nCould not find the following {len(not_found)} tracks on Spotify:")
            for title in not_found:
                print(f"- {title}")

def main():
    print("=== Spotify Playlist Creator ===\n")
    
    try:
        creator = SpotifyPlaylistCreator()
        
        # Get folder path from user input
        while True:
            folder_path = input("Enter the path to your music folder: ").strip('"')
            if os.path.isdir(folder_path):
                break
            print("Invalid directory. Please try again.")
        
        # Get playlist name from user input
        playlist_name = input("Enter a name for your playlist (or press Enter to use folder name): ").strip()
        
        # Ask for dry run
        dry_run = input("\nRun in dry-run mode? (y/n, default: y): ").strip().lower()
        dry_run = dry_run != 'n'  # Default to True (dry run) unless 'n' is explicitly entered
        
        # Create playlist
        creator.create_playlist_from_folder(
            folder_path=folder_path,
            playlist_name=playlist_name if playlist_name else None,
            public=True,
            dry_run=dry_run
        )
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        print("\nMake sure you have:")
        print("1. Created a Spotify Developer account and set up an application")
        print("2. Set up the .env file with your Spotify API credentials")
        print("3. Added the redirect URI to your Spotify Developer Dashboard")
        print("4. Installed all required dependencies (run 'pip install -r requirements.txt')")

if __name__ == "__main__":
    main()
