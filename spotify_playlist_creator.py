import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

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
        audio_extensions = ('.mp3', '.wav', '.flac', '.m4a')
        return [f for f in Path(folder_path).rglob('*') if f.suffix.lower() in audio_extensions]
    
    def get_song_info(self, file_path):
        """Extract song information from audio file metadata."""
        try:
            audio = MP3(file_path, ID3=ID3)
            return {
                'title': str(audio.tags.get('TIT2', '')).strip() or file_path.stem,
                'artist': str(audio.tags.get('TPE1', '')).strip(),
                'album': str(audio.tags.get('TALB', '')).strip(),
                'file_path': str(file_path)
            }
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")
            return {
                'title': file_path.stem,
                'artist': '',
                'album': '',
                'file_path': str(file_path)
            }
    
    def search_spotify_track(self, song_info):
        """Search for a track on Spotify."""
        query_parts = []
        if song_info['title']:
            query_parts.append(f"track:{song_info['title']}")
        if song_info['artist']:
            query_parts.append(f"artist:{song_info['artist']}")
        
        if not query_parts:
            return None
            
        query = ' '.join(query_parts)
        
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'uri': track['uri']
                }
        except Exception as e:
            print(f"Error searching for {query}: {e}")
        
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
