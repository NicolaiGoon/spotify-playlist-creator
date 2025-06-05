import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import the main class from our new src structure
from src.spotify_client import SpotifyPlaylistCreator

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description='Create a Spotify playlist from a folder of music.')
    parser.add_argument('folder_path', type=str, help='Path to the folder containing music files.')
    parser.add_argument('-n', '--name', dest='playlist_name', type=str, default=None, 
                        help='Name for the Spotify playlist. Defaults to the folder name.')
    parser.add_argument('--private', action='store_true', 
                        help='Make the playlist private. Default is public.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Scan files and search Spotify, but do not create any playlists or add tracks.')

    args = parser.parse_args()

    folder_to_scan = str(Path(args.folder_path).resolve())
    playlist_is_public = not args.private

    try:
        print("Initializing Spotify Playlist Creator...")
        creator = SpotifyPlaylistCreator()
        print("Initialization complete.")
        
        creator.create_playlist_from_folder(
            folder_path=folder_to_scan,
            playlist_name=args.playlist_name,
            public=playlist_is_public,
            dry_run=args.dry_run
        )
    except ValueError as e:
        print(f"Configuration or Input Error: {e}")
    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"An unexpected error occurred: {e}")
        # For debugging, you might want to re-raise or log the traceback
        # import traceback
        # print(traceback.format_exc())

if __name__ == "__main__":
    main()
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
