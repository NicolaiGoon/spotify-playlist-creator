import os
from .metadata_utils import get_audio_files, get_song_info
from .track_finder import TrackFinder
from .spotify_client import SpotifyClient

class PlaylistCreator:
    def __init__(self, spotify_client: SpotifyClient):
        self.spotify_client = spotify_client
        self.track_finder = TrackFinder(spotify_client.sp)

    def _process_audio_files(self, audio_files):
        """Process audio files to find them on Spotify."""
        found_tracks_uris = []
        not_found_tracks_info = []
        for audio_file in audio_files:
            song_info = get_song_info(audio_file)
            track = self.track_finder.search_spotify_track(song_info)
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
            playlist = self.spotify_client.create_playlist(playlist_name, public=public)
            self.spotify_client.add_tracks_to_playlist(playlist['id'], found_tracks_uris)
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
        audio_files = get_audio_files(folder_path)
        
        if not audio_files:
            print("No audio files found in the folder.")
            return

        print(f"Found {len(audio_files)} audio files. Processing...")
        
        found_tracks_uris, not_found_tracks_info = self._process_audio_files(audio_files)
        
        self._print_summary(len(found_tracks_uris), not_found_tracks_info)
        
        self._handle_playlist_creation(playlist_name, public, found_tracks_uris, dry_run)
